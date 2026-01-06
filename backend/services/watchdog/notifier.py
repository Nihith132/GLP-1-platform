"""
Notifier Service
Sends alerts via Slack and Email
"""

import httpx
import os
from typing import List, Dict
from datetime import datetime


class Notifier:
    """Handles notifications for watchdog events"""
    
    def __init__(self):
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.notification_emails = os.getenv('NOTIFICATION_EMAILS', '').split(',')
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def send_summary(
        self,
        new_versions: List[Dict],
        up_to_date: List[Dict],
        errors: List[Dict],
        mode: str
    ):
        """
        Send summary notification after watchdog run
        """
        # Build message
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        message_blocks = [
            f"🐕 *Watchdog Pipeline Summary*",
            f"_Run: {timestamp} | Mode: {mode.upper()}_",
            f""
        ]
        
        if new_versions:
            message_blocks.append(f"🆕 *{len(new_versions)} New Version(s) Detected:*")
            for v in new_versions:
                message_blocks.append(
                    f"   • {v['drug_name']}\n"
                    f"      {v['current_version']} → {v['new_version']}\n"
                    f"      Published: {v.get('publish_date', 'Unknown')}"
                )
            message_blocks.append("")
        
        if up_to_date:
            message_blocks.append(f"✅ *{len(up_to_date)} Drug(s) Up to Date*")
            message_blocks.append("")
        
        if errors:
            message_blocks.append(f"❌ *{len(errors)} Error(s):*")
            for e in errors:
                message_blocks.append(
                    f"   • {e.get('drug_name', e.get('set_id', 'Unknown'))}\n"
                    f"      Error: {e.get('error', 'Unknown error')}"
                )
            message_blocks.append("")
        
        message_text = "\n".join(message_blocks)
        
        # Send to Slack
        if self.slack_webhook:
            await self._send_slack(message_text)
        
        # Send to Email
        if self.sendgrid_api_key and self.notification_emails:
            await self._send_email(
                subject=f"Watchdog Report: {len(new_versions)} New Version(s)",
                body=message_text
            )
    
    async def send_error(
        self,
        error_message: str,
        mode: str,
        set_id: str = None
    ):
        """
        Send error notification
        """
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        message = (
            f"🚨 *Watchdog Pipeline FAILED*\n"
            f"_Time: {timestamp} | Mode: {mode.upper()}_\n\n"
            f"**Error:**\n{error_message}\n\n"
        )
        
        if set_id:
            message += f"SET_ID: {set_id}\n"
        
        # Send to Slack
        if self.slack_webhook:
            await self._send_slack(message)
        
        # Send to Email
        if self.sendgrid_api_key and self.notification_emails:
            await self._send_email(
                subject="🚨 Watchdog Pipeline FAILED",
                body=message
            )
    
    async def _send_slack(self, message: str):
        """Send message to Slack webhook"""
        try:
            payload = {
                "text": message,
                "username": "Watchdog Bot",
                "icon_emoji": ":dog:"
            }
            
            response = await self.http_client.post(
                self.slack_webhook,
                json=payload
            )
            
            if response.status_code == 200:
                print("   ✓ Slack notification sent")
            else:
                print(f"   ⚠️  Slack notification failed: {response.status_code}")
        
        except Exception as e:
            print(f"   ⚠️  Slack error: {str(e)}")
    
    async def _send_email(self, subject: str, body: str):
        """Send email via SendGrid"""
        try:
            # SendGrid API v3
            url = "https://api.sendgrid.com/v3/mail/send"
            
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": email.strip()} for email in self.notification_emails if email.strip()],
                        "subject": subject
                    }
                ],
                "from": {
                    "email": "watchdog@yourdomain.com",
                    "name": "Label Analyzer Watchdog"
                },
                "content": [
                    {
                        "type": "text/plain",
                        "value": body
                    }
                ]
            }
            
            response = await self.http_client.post(
                url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 202:
                print(f"   ✓ Email sent to {len(self.notification_emails)} recipient(s)")
            else:
                print(f"   ⚠️  Email failed: {response.status_code}")
        
        except Exception as e:
            print(f"   ⚠️  Email error: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
