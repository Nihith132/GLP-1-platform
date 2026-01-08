"""
Version Check API Routes
Endpoints for checking label versions and viewing version history
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime

from api.schemas import VersionCheckResult, VersionHistory
from models.db_session import AsyncSessionLocal
from services.watchdog.version_checker import VersionChecker

router = APIRouter()


@router.post("/trigger/{drug_id}/", response_model=VersionCheckResult)
async def trigger_version_check(drug_id: int):
    """
    Trigger a manual version check for a specific drug
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get drug info
            query = text("""
                SELECT id, set_id, name, version
                FROM drug_labels
                WHERE id = :drug_id
            """)
            result = await session.execute(query, {"drug_id": drug_id})
            drug = result.fetchone()
            
            if not drug:
                raise HTTPException(status_code=404, detail="Drug not found")
            
            # Check version
            checker = VersionChecker()
            result = await checker.check_version(
                session,
                set_id=drug.set_id,
                current_version=drug.version
            )
            
            # Return result
            return VersionCheckResult(
                drug_id=drug_id,
                drug_name=drug.name,
                current_version=drug.version,
                new_version=result.get("new_version"),
                has_update=result.get("has_update", False),
                changes=result.get("changes"),
                checked_at=datetime.now()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking version: {str(e)}"
            )


@router.post("/", response_model=List[VersionCheckResult])
async def check_versions(drug_ids: Optional[List[int]] = None):
    """
    Check versions for multiple drugs
    If drug_ids is not provided, checks all enabled drugs
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get drugs to check
            if drug_ids:
                query = text("""
                    SELECT id, set_id, name, version
                    FROM drug_labels
                    WHERE id = ANY(:drug_ids)
                """)
                result = await session.execute(query, {"drug_ids": drug_ids})
            else:
                query = text("""
                    SELECT id, set_id, name, version
                    FROM drug_labels
                    WHERE version_check_enabled = true
                """)
                result = await session.execute(query)
            
            drugs = result.fetchall()
            
            if not drugs:
                return []
            
            # Check each drug
            checker = VersionChecker()
            results = []
            
            for drug in drugs:
                try:
                    check_result = await checker.check_version(
                        session,
                        set_id=drug.set_id,
                        current_version=drug.version
                    )
                    
                    results.append(VersionCheckResult(
                        drug_id=drug.id,
                        drug_name=drug.name,
                        current_version=drug.version,
                        new_version=check_result.get("new_version"),
                        has_update=check_result.get("has_update", False),
                        changes=check_result.get("changes"),
                        checked_at=datetime.now()
                    ))
                except Exception as e:
                    print(f"Error checking {drug.name}: {e}")
                    results.append(VersionCheckResult(
                        drug_id=drug.id,
                        drug_name=drug.name,
                        current_version=drug.version,
                        new_version=None,
                        has_update=False,
                        changes=f"Error: {str(e)}",
                        checked_at=datetime.now()
                    ))
            
            return results
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking versions: {str(e)}"
            )


@router.get("/history/{drug_id}/", response_model=List[VersionHistory])
async def get_version_history(drug_id: int):
    """
    Get version history for a specific drug
    """
    async with AsyncSessionLocal() as session:
        try:
            query = text("""
                SELECT 
                    vh.id,
                    vh.drug_id,
                    dl.name as drug_name,
                    vh.old_version,
                    vh.new_version,
                    vh.changes_detected,
                    vh.checked_at,
                    vh.updated_at
                FROM version_history vh
                JOIN drug_labels dl ON vh.drug_id = dl.id
                WHERE vh.drug_id = :drug_id
                ORDER BY vh.checked_at DESC
                LIMIT 50
            """)
            
            result = await session.execute(query, {"drug_id": drug_id})
            history = result.fetchall()
            
            return [
                VersionHistory(
                    id=row.id,
                    drug_id=row.drug_id,
                    drug_name=row.drug_name,
                    old_version=row.old_version,
                    new_version=row.new_version,
                    changes_detected=row.changes_detected,
                    checked_at=row.checked_at,
                    updated_at=row.updated_at
                )
                for row in history
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching version history: {str(e)}"
            )
