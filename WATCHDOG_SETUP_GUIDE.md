# Watchdog Pipeline - Step-by-Step Setup Guide

## 📋 Overview
This guide will walk you through setting up the automated Watchdog Pipeline that monitors DailyMed for label version updates using GitHub Actions.

---

## ✅ Step 1: Run Database Migration

First, add the necessary database tables and columns:

```bash
cd /Users/nihithreddy/slickbit\ label\ analyzer/backend
python scripts/migrations/add_watchdog_tables.py
```

**What this does:**
- Adds 3 new columns to `drugs` table:
  - `current_label_version` (VARCHAR)
  - `version_check_enabled` (BOOLEAN)
  - `last_version_check` (TIMESTAMP)
- Creates `drug_version_history` table to track all version changes
- Creates 4 indexes for query performance

**Verify migration:**
```sql
-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'drugs' 
AND column_name IN ('current_label_version', 'version_check_enabled', 'last_version_check');

-- Check version history table exists
SELECT COUNT(*) FROM drug_version_history;
```

---

## ✅ Step 2: Enable Version Checking for Drugs

Choose which drugs should be monitored and enable them:

```sql
-- Example: Enable checking for SAXENDA
UPDATE drugs 
SET version_check_enabled = true,
    current_label_version = '8'  -- Optional: set current version
WHERE set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15';

-- Enable multiple drugs at once
UPDATE drugs 
SET version_check_enabled = true
WHERE drug_name IN ('SAXENDA', 'OZEMPIC', 'WEGOVY');
```

**Note:** If you don't set `current_label_version`, the watchdog will auto-detect it on first run and save it.

---

## ✅ Step 3: Install Required Python Packages

Add these to your `requirements.txt` if not already present:

```txt
boto3>=1.28.0        # AWS S3 integration
httpx>=0.24.0        # Async HTTP client for DailyMed API
```

Install them:
```bash
pip install boto3 httpx
```

---

## ✅ Step 4: Set Up AWS S3 (If Not Already Done)

### Option A: Use Existing S3 Bucket
If you already have an S3 bucket, note down:
- Bucket name
- AWS Access Key ID
- AWS Secret Access Key
- AWS Region

### Option B: Create New S3 Bucket
1. Go to AWS Console → S3
2. Click "Create bucket"
3. Bucket name: `slickbit-label-analyzer` (or your choice)
4. Region: `us-east-1` (or your preferred region)
5. Keep default settings, click "Create bucket"

### Create IAM User for GitHub Actions
1. AWS Console → IAM → Users → "Create user"
2. Username: `github-actions-watchdog`
3. Attach policy: `AmazonS3FullAccess` (or create custom policy)
4. Create access key → "Application running outside AWS"
5. **Save Access Key ID and Secret Access Key** (you won't see them again!)

---

## ✅ Step 5: Set Up GitHub Secrets

Navigate to your GitHub repository:
```
https://github.com/Nihith132/GLP-1-platform/settings/secrets/actions
```

Click "New repository secret" and add these **8 secrets**:

| Secret Name | Value | Example |
|------------|-------|---------|
| `DATABASE_URL` | Your PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `AWS_ACCESS_KEY_ID` | From Step 4 | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | From Step 4 | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | Your S3 region | `us-east-1` |
| `S3_BUCKET_NAME` | Your bucket name | `slickbit-label-analyzer` |
| `SLACK_WEBHOOK_URL` | (Optional) Slack webhook | `https://hooks.slack.com/services/...` |
| `SENDGRID_API_KEY` | (Optional) SendGrid key | `SG.xxxxx` |
| `NOTIFICATION_EMAILS` | (Optional) Comma-separated emails | `admin@company.com,team@company.com` |

**Important:** 
- First 5 secrets are **required**
- Last 3 are **optional** (for notifications)

---

## ✅ Step 6: Set Up Slack Notifications (Optional)

If you want Slack alerts:

1. Go to your Slack workspace
2. Navigate to: https://api.slack.com/messaging/webhooks
3. Click "Create New Webhook"
4. Choose a channel (e.g., `#label-alerts`)
5. Copy the webhook URL
6. Add to GitHub Secrets as `SLACK_WEBHOOK_URL`

---

## ✅ Step 7: Set Up Email Notifications (Optional)

If you want email alerts:

### Using SendGrid (Free 100 emails/day):
1. Sign up: https://sendgrid.com/
2. Create API Key: Settings → API Keys → Create API Key
3. Permissions: "Full Access" or "Mail Send"
4. Copy API key
5. Add to GitHub Secrets as `SENDGRID_API_KEY`
6. Add recipient emails as `NOTIFICATION_EMAILS` (comma-separated)

---

## ✅ Step 8: Push Workflow Files to GitHub

The workflow files are already created in your workspace:
```
.github/workflows/watchdog-daily.yml      # Automatic daily checks
.github/workflows/watchdog-manual.yml     # Manual trigger
```

Push them to GitHub:

```bash
cd /Users/nihithreddy/slickbit\ label\ analyzer

# Check git status
git status

# Add workflow files
git add .github/workflows/watchdog-daily.yml
git add .github/workflows/watchdog-manual.yml

# Add Python scripts and services
git add backend/scripts/run_watchdog.py
git add backend/scripts/migrations/add_watchdog_tables.py
git add backend/services/watchdog/

# Commit
git commit -m "Add Watchdog Pipeline with GitHub Actions"

# Push to GitHub
git push origin main
```

---

## ✅ Step 9: Test the Pipeline Manually

Before waiting for the scheduled run, test it manually:

1. Go to your GitHub repository
2. Navigate to: **Actions** tab
3. Click on: **"Watchdog Manual Trigger"** workflow
4. Click: **"Run workflow"** button (top right)
5. Fill in parameters:
   - **set_id**: Leave empty (to check all enabled drugs) OR enter specific SET_ID
   - **mode**: Select "manual"
   - **force_download**: Leave unchecked
6. Click: **"Run workflow"**

---

## ✅ Step 10: Monitor the Run

Watch the workflow execution:

1. The workflow will appear in the Actions tab
2. Click on the running workflow to see live logs
3. Watch each step execute:
   - ✓ Checkout repository
   - ✓ Setup Python
   - ✓ Install dependencies
   - ✓ Run Watchdog Pipeline
   - ✓ Upload logs

**Expected output in logs:**
```
============================================================
🐕 Watchdog Pipeline Started - 2026-01-06T12:00:00
Mode: MANUAL
============================================================

📋 Step 1: Fetching drugs to check...
   ✓ Found 3 enabled drugs

🔍 Step 2: Checking versions via DailyMed API...

   Checking: SAXENDA (SET_ID: 2160dee6-dc44-4639-af3f-fd1ac2a32d15)
      ✓ Up to date: 8

📧 Step 4: Sending notifications...
   ℹ️  No notifications needed (all up to date)

============================================================
✅ Watchdog Pipeline Completed
============================================================
Duration: 15.32 seconds
New Versions: 0
Up to Date: 3
Errors: 0
============================================================
```

---

## ✅ Step 11: Configure Schedule (Already Done!)

The daily workflow is already configured to run at:
- **2 AM UTC** (Coordinated Universal Time)
- Which is **9 AM IST** (India) or **6 PM PST** (Pacific)

To change the schedule, edit `.github/workflows/watchdog-daily.yml`:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Change this line
```

**Common cron schedules:**
```
'0 2 * * *'      # Daily at 2 AM UTC
'0 */6 * * *'    # Every 6 hours
'0 9 * * 1-5'    # Weekdays at 9 AM UTC
'0 0 1 * *'      # Monthly on 1st at midnight
```

---

## 📊 Step 12: View Results

### Check Slack/Email
If configured, you'll receive notifications when:
- ✅ New versions detected
- ❌ Errors occur
- 📊 Weekly summary (Sundays)

### Check Database
View version history:
```sql
SELECT 
    d.drug_name,
    v.old_version,
    v.new_version,
    v.publish_date,
    v.detected_at,
    v.s3_key
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
ORDER BY v.detected_at DESC
LIMIT 10;
```

### Check S3
New labels are uploaded to:
```
s3://your-bucket/labels/active/{SET_ID}/v{VERSION}/...
```

### Check GitHub Actions Logs
- Go to Actions tab
- Click on any workflow run
- Download artifact logs (kept for 90 days)

---

## 🔧 Troubleshooting

### Issue: "Database connection failed"
**Solution:** Check `DATABASE_URL` secret format:
```
postgresql://username:password@host:port/database
```

### Issue: "S3 upload failed - Access Denied"
**Solution:** Verify IAM user has S3 permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::your-bucket/*",
        "arn:aws:s3:::your-bucket"
      ]
    }
  ]
}
```

### Issue: "No drugs to check"
**Solution:** Enable drugs in database:
```sql
UPDATE drugs SET version_check_enabled = true WHERE set_id = 'your-set-id';
```

### Issue: "DailyMed API timeout"
**Solution:** This is normal for large labels. The workflow has 30-minute timeout.

### Issue: "Slack notification failed"
**Solution:** Test webhook URL:
```bash
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"Test message"}' \
YOUR_SLACK_WEBHOOK_URL
```

---

## 🎯 What Happens Next?

### Daily Automatic Checks (2 AM UTC)
1. GitHub Actions triggers workflow
2. Checks all enabled drugs on DailyMed
3. Downloads new versions (if any)
4. Uploads to S3
5. Updates database
6. Sends notifications
7. Logs stored for 90 days

### When New Version Detected
1. **Immediate notification** via Slack/Email
2. **ZIP downloaded** from DailyMed
3. **Uploaded to S3**: `labels/active/{SET_ID}/v{VERSION}/`
4. **Database updated**: 
   - `drugs.current_label_version` = new version
   - New row in `drug_version_history`
5. **Old versions archived** (keeps last 5 in active/)

### Manual Triggers
You can run checks anytime via GitHub Actions → "Run workflow"

---

## 📈 Monitoring Best Practices

1. **Weekly Review**: Check GitHub Actions runs every Monday
2. **Database Audit**: Review `drug_version_history` monthly
3. **S3 Cleanup**: Archive old versions after 6 months
4. **Cost Monitoring**: Check AWS billing (S3 storage costs)
5. **Enable More Drugs**: Gradually enable version checking for more drugs

---

## 🚀 Next Steps (Future Enhancements)

After basic setup is working, you can add:

1. **ETL Pipeline Integration**: Auto-process new labels through existing pipeline
2. **Comparison Dashboard**: Compare new vs old versions
3. **Version Diff Tool**: Highlight changes between versions
4. **Approval Workflow**: Require manual approval before processing
5. **Multi-Region**: Add backup S3 buckets in different regions

---

## 💡 Tips

- **Start small**: Enable 2-3 drugs first, test for a week
- **Check logs**: Download artifact logs to debug issues
- **Monitor costs**: S3 + GitHub Actions are cheap but monitor usage
- **Backup secrets**: Keep credentials in password manager
- **Document changes**: Update this guide as you customize

---

## ✅ Success Checklist

- [ ] Database migration completed
- [ ] At least 1 drug enabled for version checking
- [ ] Python packages installed (boto3, httpx)
- [ ] AWS S3 bucket created
- [ ] All 8 GitHub Secrets configured
- [ ] Workflow files pushed to GitHub
- [ ] Manual test run successful
- [ ] Daily schedule configured
- [ ] Notifications working (Slack/Email)
- [ ] Logs accessible in GitHub Actions

---

**You're all set! The watchdog is now monitoring your labels 🐕**
