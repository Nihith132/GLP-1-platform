"""
Version Checker Service
Interfaces with DailyMed API to check label versions
"""

import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import text
from pathlib import Path
import zipfile
import tempfile


class VersionChecker:
    """Checks DailyMed API for label version updates"""
    
    DAILYMED_API_BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_enabled_drugs(self, session) -> List[Dict]:
        """
        Get all drugs with version_check_enabled=true
        
        Returns list of dicts with drug_id, set_id, drug_name, current_version
        """
        query = text("""
            SELECT 
                id as drug_id,
                set_id,
                name as drug_name,
                version as current_version
            FROM drug_labels
            WHERE version_check_enabled = true
            ORDER BY name
        """)
        
        result = await session.execute(query)
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_specific_drug(self, session, set_id: str) -> List[Dict]:
        """Get specific drug by SET_ID for manual checks"""
        query = text("""
            SELECT 
                id as drug_id,
                set_id,
                name as drug_name,
                version as current_version
            FROM drug_labels
            WHERE set_id = :set_id
        """)
        
        result = await session.execute(query, {"set_id": set_id})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    
    async def check_version(
        self, 
        drug_id: int, 
        set_id: str, 
        current_version: Optional[str]
    ) -> Dict:
        """
        Check if new version exists on DailyMed
        
        Returns dict with status: 'new_version', 'up_to_date', or 'error'
        """
        try:
            # Get SPL metadata from DailyMed
            url = f"{self.DAILYMED_API_BASE}/spls/{set_id}.json"
            response = await self.client.get(url)
            
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'drug_id': drug_id,
                    'set_id': set_id,
                    'error': f"DailyMed API returned {response.status_code}"
                }
            
            data = response.json()
            metadata = data.get('data', {}).get('spl', {})
            
            # Extract version and publish date
            new_version = metadata.get('version_number')
            publish_date = metadata.get('published_date')
            drug_name = metadata.get('title', 'Unknown')
            
            if not new_version:
                return {
                    'status': 'error',
                    'drug_id': drug_id,
                    'set_id': set_id,
                    'drug_name': drug_name,
                    'error': 'No version number in DailyMed response'
                }
            
            # Compare versions
            if current_version != new_version:
                return {
                    'status': 'new_version',
                    'drug_id': drug_id,
                    'set_id': set_id,
                    'drug_name': drug_name,
                    'current_version': current_version,
                    'new_version': new_version,
                    'publish_date': publish_date
                }
            else:
                return {
                    'status': 'up_to_date',
                    'drug_id': drug_id,
                    'set_id': set_id,
                    'drug_name': drug_name,
                    'current_version': current_version
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'drug_id': drug_id,
                'set_id': set_id,
                'error': str(e)
            }
    
    async def download_label_zip(
        self, 
        set_id: str, 
        version: str
    ) -> Optional[Path]:
        """
        Download label ZIP from DailyMed
        
        Returns path to downloaded ZIP file in temp directory
        """
        try:
            # DailyMed ZIP download URL
            url = f"{self.DAILYMED_API_BASE}/spls/{set_id}/media.zip"
            
            print(f"         Downloading from: {url}")
            response = await self.client.get(url)
            
            if response.status_code != 200:
                print(f"         Error: HTTP {response.status_code}")
                return None
            
            # Save to temp file
            temp_dir = Path(tempfile.gettempdir()) / "watchdog_downloads"
            temp_dir.mkdir(exist_ok=True)
            
            zip_path = temp_dir / f"{set_id}_v{version}.zip"
            zip_path.write_bytes(response.content)
            
            # Verify it's a valid ZIP
            if not zipfile.is_zipfile(zip_path):
                print(f"         Error: Downloaded file is not a valid ZIP")
                zip_path.unlink()
                return None
            
            return zip_path
        
        except Exception as e:
            print(f"         Download error: {str(e)}")
            return None
    
    async def save_version_update(
        self,
        session,
        drug_id: int,
        old_version: Optional[str],
        new_version: str,
        s3_key: str,
        publish_date: Optional[str]
    ):
        """
        Save version update to database
        
        Updates drug_labels.version and inserts into drug_version_history
        """
        try:
            # Update current version in drug_labels table
            update_drug = text("""
                UPDATE drug_labels
                SET version = :new_version,
                    last_version_check = :now
                WHERE id = :drug_id
            """)
            await session.execute(update_drug, {
                "new_version": new_version,
                "now": datetime.utcnow(),
                "drug_id": drug_id
            })
            
            # Insert version history record
            insert_history = text("""
                INSERT INTO drug_version_history (
                    drug_id, old_version, new_version, s3_key, 
                    publish_date, detected_at
                )
                VALUES (
                    :drug_id, :old_version, :new_version, :s3_key,
                    :publish_date, :detected_at
                )
            """)
            await session.execute(insert_history, {
                "drug_id": drug_id,
                "old_version": old_version,
                "new_version": new_version,
                "s3_key": s3_key,
                "publish_date": publish_date,
                "detected_at": datetime.utcnow()
            })
            
            await session.commit()
        
        except Exception as e:
            await session.rollback()
            raise Exception(f"Database update failed: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
