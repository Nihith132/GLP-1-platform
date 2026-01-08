"""
Script to clear all highlights from saved reports
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.db_session import AsyncSessionLocal
from models.schemas import Report
from sqlalchemy import select

async def clear_highlights():
    """Clear all highlights from workspace_state in all reports"""
    async with AsyncSessionLocal() as db:
        try:
            # Get all reports
            result = await db.execute(select(Report))
            reports = result.scalars().all()
            
            cleared_count = 0
            for report in reports:
                workspace_state = report.workspace_state
                
                # Clear highlights based on report type
                if report.report_type == 'comparison':
                    if 'source_highlights' in workspace_state:
                        workspace_state['source_highlights'] = []
                        cleared_count += 1
                    # Also clear cited notes
                    if 'cited_notes' in workspace_state:
                        workspace_state['cited_notes'] = []
                else:  # analysis
                    if 'highlights' in workspace_state:
                        workspace_state['highlights'] = []
                        cleared_count += 1
                    # Clear cited notes in analysis workspace
                    if 'notes' in workspace_state:
                        # Filter out cited notes
                        workspace_state['notes'] = {
                            k: v for k, v in workspace_state['notes'].items()
                            if v.get('type') != 'cited'
                        }
                
                # Update the report
                report.workspace_state = workspace_state
                db.add(report)
            
            await db.commit()
            print(f"✅ Successfully cleared highlights from {cleared_count} reports")
            print(f"   Total reports processed: {len(reports)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(clear_highlights())
