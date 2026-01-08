"""
Test SendGrid Email Configuration
"""

import asyncio
import os
import httpx
from datetime import datetime


async def test_sendgrid():
    """Test SendGrid API and email sending"""
    
    print("=" * 70)
    print("🔍 SENDGRID CONFIGURATION TEST")
    print("=" * 70)
    
    # Check environment variables
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    notification_emails = os.getenv('NOTIFICATION_EMAILS', '')
    
    print("\n1️⃣  Environment Variables:")
    print(f"   SENDGRID_API_KEY: {'✅ Set' if sendgrid_api_key else '❌ Not set'}")
    if sendgrid_api_key:
        print(f"   Key length: {len(sendgrid_api_key)} characters")
        print(f"   Key prefix: {sendgrid_api_key[:10]}...")
    
    print(f"\n   NOTIFICATION_EMAILS: {'✅ Set' if notification_emails else '❌ Not set'}")
    if notification_emails:
        emails = [e.strip() for e in notification_emails.split(',') if e.strip()]
        print(f"   Recipients: {len(emails)}")
        for email in emails:
            print(f"      • {email}")
    
    if not sendgrid_api_key:
        print("\n❌ SendGrid API key not found!")
        print("   Set it with: export SENDGRID_API_KEY='your-api-key'")
        return False
    
    if not notification_emails:
        print("\n⚠️  Warning: No notification emails configured!")
        print("   Set with: export NOTIFICATION_EMAILS='email1@example.com,email2@example.com'")
    
    # Test SendGrid API connectivity
    print("\n2️⃣  Testing SendGrid API Connectivity...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test API key validity with sender verification endpoint
            headers = {
                "Authorization": f"Bearer {sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            # Get account details
            response = await client.get(
                "https://api.sendgrid.com/v3/user/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                profile = response.json()
                print(f"   ✅ API Key Valid!")
                print(f"   Account: {profile.get('username', 'N/A')}")
                print(f"   Email: {profile.get('email', 'N/A')}")
            elif response.status_code == 401:
                print(f"   ❌ Invalid API Key!")
                print(f"   Status: {response.status_code}")
                return False
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                print(f"   Body: {response.text[:200]}")
    
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
        return False
    
    # Send test email if emails are configured
    if notification_emails:
        print("\n3️⃣  Sending Test Email...")
        
        try:
            emails = [e.strip() for e in notification_emails.split(',') if e.strip()]
            
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": email} for email in emails],
                        "subject": "✅ Watchdog Test Email - Configuration Successful"
                    }
                ],
                "from": {
                    "email": "watchdog@yourdomain.com",
                    "name": "Label Analyzer Watchdog"
                },
                "content": [
                    {
                        "type": "text/plain",
                        "value": f"""
🐕 Watchdog Pipeline - Test Email

This is a test email to verify your SendGrid configuration.

Timestamp: {timestamp}
Recipients: {', '.join(emails)}

If you received this email, your SendGrid integration is working correctly!

---
GLP-1 Regulatory Intelligence Platform
Automated Label Monitoring System
"""
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 202:
                    print(f"   ✅ Test email sent successfully!")
                    print(f"   Recipients: {', '.join(emails)}")
                    print(f"   Status: {response.status_code} (Accepted)")
                    print("\n   📧 Check your inbox!")
                else:
                    print(f"   ❌ Failed to send email")
                    print(f"   Status: {response.status_code}")
                    print(f"   Response: {response.text[:500]}")
                    return False
        
        except Exception as e:
            print(f"   ❌ Error sending email: {str(e)}")
            return False
    
    print("\n" + "=" * 70)
    print("✅ SENDGRID CONFIGURATION TEST PASSED")
    print("=" * 70)
    print("\n✨ Your email notifications are ready!")
    print("   • Daily reports will be sent at 2:00 AM IST (8:30 PM UTC)")
    print("   • New version alerts will be emailed immediately")
    print("   • Error notifications will be sent if pipeline fails")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_sendgrid())
    exit(0 if success else 1)
