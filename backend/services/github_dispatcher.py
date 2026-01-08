"""
GitHub Actions Workflow Dispatcher
Triggers the watchdog-manual.yml workflow via GitHub API
"""

import httpx
import os
from typing import List, Optional
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)


class GitHubDispatcher:
    """Dispatches GitHub Actions workflows"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER', 'Nihith132')
        self.repo_name = os.getenv('GITHUB_REPO_NAME', 'GLP-1-platform')
        self.workflow_file = 'watchdog-manual.yml'
        
        if not self.github_token:
            print("⚠️ WARNING: GITHUB_TOKEN not set - workflow dispatch will fail")
    
    async def trigger_workflow(
        self, 
        set_ids: List[str], 
        mode: str = 'manual',
        force_download: bool = False
    ) -> dict:
        """
        Trigger the GitHub Actions workflow
        
        Args:
            set_ids: List of SET_IDs to check (only first one used in manual mode)
            mode: 'manual' or 'daily'
            force_download: Force download even if version unchanged
            
        Returns:
            dict with status and details
        """
        if not self.github_token:
            return {
                'status': 'error',
                'message': 'GITHUB_TOKEN not configured'
            }
        
        # For manual mode, use the first SET_ID
        set_id = set_ids[0] if set_ids else None
        
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{self.workflow_file}/dispatches"
        
        headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        payload = {
            'ref': 'main',  # or your default branch
            'inputs': {
                'set_id': set_id or '',
                'mode': mode,
                'force_download': str(force_download).lower()
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 204:
                    # Success - GitHub returns 204 No Content
                    return {
                        'status': 'success',
                        'message': f'Workflow triggered successfully for {len(set_ids)} drug(s)',
                        'set_ids': set_ids,
                        'mode': mode,
                        'workflow_url': f'https://github.com/{self.repo_owner}/{self.repo_name}/actions/workflows/{self.workflow_file}'
                    }
                else:
                    error_detail = response.text
                    return {
                        'status': 'error',
                        'message': f'GitHub API returned {response.status_code}',
                        'detail': error_detail
                    }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to trigger workflow: {str(e)}'
            }
    
    async def trigger_for_multiple_drugs(
        self, 
        set_ids: List[str],
        force_download: bool = False
    ) -> List[dict]:
        """
        Trigger workflow for multiple drugs (sequentially)
        Each drug gets its own workflow run
        
        Returns:
            List of result dicts
        """
        results = []
        
        for set_id in set_ids:
            result = await self.trigger_workflow(
                set_ids=[set_id],
                mode='manual',
                force_download=force_download
            )
            results.append(result)
            
            # Small delay between triggers to avoid rate limiting
            await asyncio.sleep(1)
        
        return results
