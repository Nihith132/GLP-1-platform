"""
Watchdog API Routes
Real-time manual triggering of version check automation via GitHub Actions
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
import asyncio
import json
from datetime import datetime

from models.db_session import AsyncSessionLocal
from services.watchdog.version_checker import VersionChecker
from services.watchdog.s3_uploader import S3Uploader
from services.github_dispatcher import GitHubDispatcher

router = APIRouter()

# Store active WebSocket connections for progress updates
active_connections: List[WebSocket] = []


class WatchdogPipeline:
    """Manages the watchdog automation pipeline with real-time progress"""
    
    def __init__(self, websocket: Optional[WebSocket] = None):
        self.websocket = websocket
        self.version_checker = VersionChecker()
        self.s3_uploader = S3Uploader()
    
    async def send_progress(self, drug_id: int, status: str, message: str, 
                          progress: int, data: dict = None):
        """Send progress update via WebSocket"""
        if self.websocket:
            update = {
                "drug_id": drug_id,
                "status": status,
                "message": message,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data or {}
            }
            try:
                await self.websocket.send_json(update)
            except Exception as e:
                print(f"Error sending WebSocket update: {e}")
    
    async def run_for_drug(self, drug_id: int, set_id: str, current_version: int):
        """
        Run the full watchdog pipeline for a single drug
        Returns: dict with results
        """
        try:
            # Step 1: Check version (0-25%)
            await self.send_progress(drug_id, "running", "Fetching label from FDA DailyMed...", 10)
            
            result = await self.version_checker.check_version(
                drug_id=drug_id,
                set_id=set_id,
                current_version=current_version
            )
            
            await self.send_progress(drug_id, "running", "Comparing versions...", 25)
            
            if result['status'] == 'up_to_date':
                await self.send_progress(
                    drug_id, "completed", "No updates available - label is current", 100,
                    {"has_update": False, "current_version": current_version}
                )
                return {
                    "drug_id": drug_id,
                    "status": "up_to_date",
                    "has_update": False,
                    "current_version": current_version
                }
            
            # Step 2: Download new version (25-50%)
            await self.send_progress(
                drug_id, "running", 
                f"New version {result['new_version']} found! Downloading...", 35
            )
            
            zip_path = await self.version_checker.download_label_zip(
                set_id=set_id,
                version=result['new_version']
            )
            
            if not zip_path:
                await self.send_progress(drug_id, "error", "Failed to download label", 100)
                return {"drug_id": drug_id, "status": "error", "error": "Download failed"}
            
            await self.send_progress(drug_id, "running", "Download complete", 50)
            
            # Step 3: Upload to S3 (50-75%)
            await self.send_progress(drug_id, "running", "Uploading to S3...", 60)
            
            s3_url = await self.s3_uploader.upload_label(
                zip_path=zip_path,
                set_id=set_id,
                version=result['new_version']
            )
            
            await self.send_progress(drug_id, "running", "S3 upload complete", 75)
            
            # Step 4: Update database (75-90%)
            await self.send_progress(drug_id, "running", "Updating database...", 85)
            
            async with AsyncSessionLocal() as session:
                await self.version_checker.save_version_update(
                    session=session,
                    drug_id=drug_id,
                    old_version=current_version,
                    new_version=result['new_version'],
                    changes_detected=result.get('changes'),
                    s3_url=s3_url
                )
                await session.commit()
            
            # Complete (100%)
            await self.send_progress(
                drug_id, "completed", 
                f"Version updated to {result['new_version']}", 100,
                {
                    "has_update": True,
                    "new_version": result['new_version'],
                    "changes": result.get('changes'),
                    "s3_url": s3_url
                }
            )
            
            return {
                "drug_id": drug_id,
                "status": "completed",
                "has_update": True,
                "new_version": result['new_version'],
                "changes": result.get('changes'),
                "s3_url": s3_url
            }
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            await self.send_progress(drug_id, "error", error_msg, 100)
            return {
                "drug_id": drug_id,
                "status": "error",
                "error": str(e)
            }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time progress updates
    Client connects here before triggering the pipeline
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("WebSocket disconnected")


async def process_drugs_background(drug_ids: List[int]):
    """Process drugs in the background and send updates via WebSocket"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        
        placeholders = ','.join([f':id{i}' for i in range(len(drug_ids))])
        query = text(f"""
            SELECT id, set_id, name, version
            FROM drug_labels
            WHERE id IN ({placeholders})
        """)
        
        params = {f'id{i}': drug_id for i, drug_id in enumerate(drug_ids)}
        result = await session.execute(query, params)
        drugs = result.fetchall()
    
    # Process each drug
    for drug in drugs:
        # Send updates to all connected WebSocket clients
        for websocket in active_connections:
            pipeline = WatchdogPipeline(websocket)
            await pipeline.run_for_drug(
                drug_id=drug.id,
                set_id=drug.set_id,
                current_version=drug.version
            )


@router.post("/trigger")
async def trigger_manual_watchdog(drug_ids: List[int]):
    """
    Trigger manual version check for specific drugs via GitHub Actions
    This dispatches the watchdog-manual.yml workflow
    
    Note: Each drug will trigger a separate workflow run
    """
    if not drug_ids:
        raise HTTPException(status_code=400, detail="No drug IDs provided")
    
    # Get drug details
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        
        placeholders = ','.join([f':id{i}' for i in range(len(drug_ids))])
        query = text(f"""
            SELECT id, set_id, name, version
            FROM drug_labels
            WHERE id IN ({placeholders})
        """)
        
        params = {f'id{i}': drug_id for i, drug_id in enumerate(drug_ids)}
        result = await session.execute(query, params)
        drugs = result.fetchall()
    
    if not drugs:
        raise HTTPException(status_code=404, detail="No drugs found")
    
    # Trigger GitHub Actions workflow for each drug
    dispatcher = GitHubDispatcher()
    set_ids = [drug.set_id for drug in drugs]
    
    # Trigger workflows
    github_results = await dispatcher.trigger_for_multiple_drugs(set_ids)
    
    # Check if any failed
    failed = [r for r in github_results if r['status'] == 'error']
    if failed:
        # Return partial success with error details
        return {
            "status": "partial",
            "message": f"Triggered {len(github_results) - len(failed)}/{len(github_results)} workflows",
            "drug_count": len(drugs),
            "drugs": [{"id": d.id, "name": d.name, "set_id": d.set_id} for d in drugs],
            "github_results": github_results,
            "errors": failed
        }
    
    # Return success
    return {
        "status": "success",
        "message": "GitHub Actions workflows triggered successfully",
        "drug_count": len(drugs),
        "drugs": [{"id": d.id, "name": d.name, "set_id": d.set_id} for d in drugs],
        "github_results": github_results,
        "workflow_url": f"https://github.com/{dispatcher.repo_owner}/{dispatcher.repo_name}/actions/workflows/{dispatcher.workflow_file}"
    }


@router.post("/run/{drug_id}")
async def run_watchdog_for_drug(drug_id: int):
    """
    Run watchdog pipeline for a single drug
    This is a synchronous endpoint that waits for completion
    Use WebSocket endpoint for real-time progress
    """
    # Get drug details
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        
        query = text("""
            SELECT id, set_id, name, version
            FROM drug_labels
            WHERE id = :drug_id
        """)
        
        result = await session.execute(query, {"drug_id": drug_id})
        drug = result.fetchone()
    
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    
    # Run pipeline without WebSocket (blocking)
    pipeline = WatchdogPipeline()
    result = await pipeline.run_for_drug(
        drug_id=drug.id,
        set_id=drug.set_id,
        current_version=drug.version
    )
    
    return result
