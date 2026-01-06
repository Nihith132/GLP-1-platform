# Watchdog Pipeline - Quick Reference

## 🚀 Quick Start Commands

### 1. Run Database Migration
```bash
cd backend
python scripts/migrations/add_watchdog_tables.py
```

### 2. Enable Drug for Monitoring
```sql
UPDATE drugs 
SET version_check_enabled = true,
    current_label_version = '8'
WHERE set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15';
```

### 3. Push to GitHub
```bash
git add .github/workflows/watchdog-*.yml
git add backend/scripts/run_watchdog.py
git add backend/services/watchdog/
git commit -m "Add Watchdog Pipeline"
git push origin main
```

### 4. Test Manually
- GitHub → Actions → "Watchdog Manual Trigger" → Run workflow

---

## 📝 Required GitHub Secrets

| Secret | Required | Example |
|--------|----------|---------|
| `DATABASE_URL` | ✅ Yes | `postgresql://user:pass@host:5432/db` |
| `AWS_ACCESS_KEY_ID` | ✅ Yes | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | ✅ Yes | `wJalrXUtnFEMI/K7MDENG/...` |
| `AWS_REGION` | ✅ Yes | `us-east-1` |
| `S3_BUCKET_NAME` | ✅ Yes | `slickbit-label-analyzer` |
| `SLACK_WEBHOOK_URL` | ⚪ Optional | `https://hooks.slack.com/...` |
| `SENDGRID_API_KEY` | ⚪ Optional | `SG.xxxxx` |
| `NOTIFICATION_EMAILS` | ⚪ Optional | `admin@company.com` |

---

## 🔍 Common SQL Queries

### View Enabled Drugs
```sql
SELECT drug_name, set_id, current_label_version, last_version_check
FROM drugs 
WHERE version_check_enabled = true;
```

### View Version History
```sql
SELECT 
    d.drug_name,
    v.old_version,
    v.new_version,
    v.detected_at,
    v.s3_key
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
ORDER BY v.detected_at DESC
LIMIT 20;
```

### Enable Multiple Drugs
```sql
UPDATE drugs 
SET version_check_enabled = true
WHERE drug_name IN ('SAXENDA', 'OZEMPIC', 'WEGOVY');
```

### Disable Drug Monitoring
```sql
UPDATE drugs 
SET version_check_enabled = false
WHERE set_id = 'your-set-id';
```

---

## 📅 Cron Schedule Examples

```yaml
'0 2 * * *'      # Daily at 2 AM UTC
'0 */6 * * *'    # Every 6 hours
'0 9 * * 1-5'    # Weekdays at 9 AM UTC
'0 0 1 * *'      # Monthly on 1st at midnight
'*/30 * * * *'   # Every 30 minutes (not recommended)
```

---

## 🐛 Troubleshooting Quick Fixes

### Database connection failed
```bash
# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://username:password@host:port/database
```

### S3 access denied
```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name/
```

### No drugs to check
```sql
-- Check if any drugs enabled
SELECT COUNT(*) FROM drugs WHERE version_check_enabled = true;
```

### Slack webhook not working
```bash
# Test webhook
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"Test"}' \
https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📊 File Structure

```
.github/workflows/
├── watchdog-daily.yml          # Scheduled daily checks
└── watchdog-manual.yml         # Manual trigger

backend/
├── scripts/
│   ├── run_watchdog.py         # Entry point
│   └── migrations/
│       └── add_watchdog_tables.py
└── services/watchdog/
    ├── __init__.py
    ├── version_checker.py      # DailyMed API
    ├── s3_uploader.py          # AWS S3
    └── notifier.py             # Slack/Email
```

---

## 🎯 Workflow Triggers

### Automatic (Daily)
- Runs at 2 AM UTC every day
- Checks all enabled drugs
- No manual intervention needed

### Manual
- Go to GitHub Actions tab
- Select "Watchdog Manual Trigger"
- Click "Run workflow"
- Options:
  - **set_id**: Specific drug (or leave empty for all)
  - **mode**: manual or daily
  - **force_download**: true/false

---

## 📈 S3 Folder Structure

```
s3://your-bucket/
├── labels/
│   ├── active/
│   │   └── {SET_ID}/
│   │       └── v{VERSION}/
│   │           └── {SET_ID}_v{VERSION}_{timestamp}.zip
│   └── archive/
│       └── {SET_ID}/
│           └── (old versions)
└── logs/
    └── watchdog/
        └── {YYYYMMDD}/
            └── watchdog_{timestamp}.log
```

---

## 💰 Cost Estimates (Monthly)

- **GitHub Actions**: Free (2,000 minutes/month)
- **S3 Storage**: ~$0.023/GB (~$2 for 100GB)
- **S3 Requests**: ~$0.005 per 1,000 requests
- **SendGrid**: Free (100 emails/day)
- **Slack**: Free
- **Total**: ~$2-5/month for typical usage

---

## 🔔 Notification Examples

### Slack Message
```
🐕 Watchdog Pipeline Summary
Run: 2026-01-06 12:00:00 UTC | Mode: DAILY

🆕 1 New Version(s) Detected:
   • SAXENDA
      8 → 9
      Published: 2026-01-05

✅ 2 Drug(s) Up to Date
```

### Email Subject
```
Watchdog Report: 1 New Version(s)
```

---

## 🛠️ Maintenance Tasks

### Weekly
- [ ] Review GitHub Actions runs
- [ ] Check notification emails/Slack

### Monthly
- [ ] Review S3 storage costs
- [ ] Audit version_history table
- [ ] Enable new drugs if needed

### Quarterly
- [ ] Archive old S3 versions (>6 months)
- [ ] Review and update documentation

---

## 📞 Support Resources

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **DailyMed API**: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
- **AWS S3 Docs**: https://docs.aws.amazon.com/s3/
- **Setup Guide**: `WATCHDOG_SETUP_GUIDE.md`

---

**Need help? Check the full setup guide or review GitHub Actions logs!**
