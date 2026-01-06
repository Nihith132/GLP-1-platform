# Watchdog Pipeline - Testing & Examples

## 🧪 Complete Testing Checklist

### Phase 1: Database Setup ✅
- [ ] Migration script runs without errors
- [ ] New columns exist in `drugs` table
- [ ] `drug_version_history` table created
- [ ] All 4 indexes created successfully

**Test Commands:**
```sql
-- Verify columns
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'drugs' 
AND column_name IN ('current_label_version', 'version_check_enabled', 'last_version_check');

-- Expected: 3 rows returned

-- Verify table
SELECT COUNT(*) FROM drug_version_history;

-- Expected: 0 (empty table initially)

-- Verify indexes
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('drugs', 'drug_version_history')
AND indexname LIKE 'idx_%';

-- Expected: 4 rows (idx_version_history_drug_id, idx_version_history_detected_at, 
--                    idx_drugs_version_check, idx_drugs_last_check)
```

---

### Phase 2: Drug Configuration ✅
- [ ] At least 1 drug enabled for monitoring
- [ ] Current version set (optional, will auto-detect)
- [ ] SET_ID is valid and exists in DailyMed

**Test Commands:**
```sql
-- Enable SAXENDA for testing
UPDATE drugs 
SET version_check_enabled = true,
    current_label_version = '8'
WHERE set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15';

-- Verify enabled
SELECT 
    drug_name, 
    set_id, 
    current_label_version,
    version_check_enabled,
    last_version_check
FROM drugs 
WHERE version_check_enabled = true;

-- Expected: 1+ rows showing enabled drugs
```

---

### Phase 3: GitHub Configuration ✅
- [ ] Workflow files exist in `.github/workflows/`
- [ ] All required secrets added to GitHub
- [ ] Repository pushed to GitHub
- [ ] Actions tab accessible

**Test Commands:**
```bash
# Check workflow files exist
ls -la .github/workflows/

# Expected output:
# watchdog-daily.yml
# watchdog-manual.yml

# Check git status
git status

# Push to GitHub
git add .github/workflows/*.yml
git add backend/scripts/run_watchdog.py
git add backend/services/watchdog/
git commit -m "Add Watchdog Pipeline"
git push origin main
```

**Verify Secrets (GitHub UI):**
1. Go to: https://github.com/YOUR_USERNAME/GLP-1-platform/settings/secrets/actions
2. Check presence of:
   - DATABASE_URL ✅
   - AWS_ACCESS_KEY_ID ✅
   - AWS_SECRET_ACCESS_KEY ✅
   - AWS_REGION ✅
   - S3_BUCKET_NAME ✅
   - (Optional: SLACK_WEBHOOK_URL, SENDGRID_API_KEY, NOTIFICATION_EMAILS)

---

### Phase 4: Manual Test Run ✅
- [ ] Workflow visible in Actions tab
- [ ] Manual trigger button works
- [ ] Workflow completes successfully
- [ ] Logs show expected output

**Test Steps:**
1. GitHub → Actions → "Watchdog Manual Trigger"
2. Click "Run workflow"
3. Parameters:
   - set_id: (leave empty for all)
   - mode: manual
   - force_download: false
4. Click "Run workflow"
5. Wait 2-5 minutes
6. Check status: Should show green ✅

**Expected Log Output:**
```
============================================================
🐕 Watchdog Pipeline Started - 2026-01-06T12:00:00
Mode: MANUAL
============================================================

📋 Step 1: Fetching drugs to check...
   ✓ Found 1 enabled drugs

🔍 Step 2: Checking versions via DailyMed API...

   Checking: SAXENDA (SET_ID: 2160dee6-dc44-4639-af3f-fd1ac2a32d15)
      ✓ Up to date: 8

📧 Step 4: Sending notifications...
   ℹ️  No notifications needed (all up to date)

============================================================
✅ Watchdog Pipeline Completed
============================================================
Duration: 12.45 seconds
New Versions: 0
Up to Date: 1
Errors: 0
============================================================
```

---

### Phase 5: Database Validation ✅
- [ ] `last_version_check` timestamp updated
- [ ] No errors in database

**Test Commands:**
```sql
-- Check updated timestamp
SELECT 
    drug_name,
    current_label_version,
    last_version_check,
    NOW() - last_version_check as time_since_check
FROM drugs 
WHERE version_check_enabled = true;

-- Expected: last_version_check should be recent (< 5 minutes ago)

-- Check for any version history entries (if new version detected)
SELECT * FROM drug_version_history 
ORDER BY detected_at DESC 
LIMIT 5;

-- Expected: Empty if no new versions, or rows if new versions detected
```

---

### Phase 6: S3 Validation ✅ (Only if new version found)
- [ ] S3 bucket accessible
- [ ] ZIP file uploaded to correct path
- [ ] File is valid ZIP

**Test Commands:**
```bash
# List S3 bucket contents
aws s3 ls s3://your-bucket-name/labels/active/ --recursive

# Expected output (if new version uploaded):
# labels/active/2160dee6-dc44-4639-af3f-fd1ac2a32d15/v9/...zip

# Download file to verify
aws s3 cp s3://your-bucket-name/labels/active/.../file.zip /tmp/test.zip

# Verify it's a valid ZIP
unzip -t /tmp/test.zip

# Expected: "No errors detected"
```

---

### Phase 7: Notification Validation ✅ (If configured)
- [ ] Slack message received (if configured)
- [ ] Email received (if configured)
- [ ] Message content accurate

**Test Slack Webhook:**
```bash
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"🧪 Test notification from Watchdog Pipeline"}' \
https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Test SendGrid Email:**
```bash
curl -X POST https://api.sendgrid.com/v3/mail/send \
-H "Authorization: Bearer YOUR_SENDGRID_API_KEY" \
-H "Content-Type: application/json" \
-d '{
  "personalizations": [{"to": [{"email": "your@email.com"}]}],
  "from": {"email": "watchdog@yourdomain.com"},
  "subject": "Test Email",
  "content": [{"type": "text/plain", "value": "Test from Watchdog"}]
}'
```

---

### Phase 8: Schedule Validation ✅
- [ ] Understand when next scheduled run occurs
- [ ] Timezone conversion correct

**Calculation:**
- Cron: `0 2 * * *` = 2 AM UTC daily
- Your timezone conversions:
  - **IST**: 2:00 UTC + 5:30 = 7:30 AM IST
  - **PST**: 2:00 UTC - 8:00 = 6:00 PM PST (previous day)
  - **EST**: 2:00 UTC - 5:00 = 9:00 PM EST (previous day)

**Next Run Calculator:**
```python
from datetime import datetime, timezone
import pytz

utc_time = datetime.now(timezone.utc).replace(hour=2, minute=0, second=0, microsecond=0)
ist = pytz.timezone('Asia/Kolkata')
pst = pytz.timezone('America/Los_Angeles')

print(f"Next UTC run: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"Next IST run: {utc_time.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"Next PST run: {utc_time.astimezone(pst).strftime('%Y-%m-%d %H:%M:%S %Z')}")
```

---

## 📊 Example SQL Queries

### Query 1: Find Drugs That Need Version Updates
```sql
-- Drugs not checked in last 7 days
SELECT 
    drug_name,
    set_id,
    current_label_version,
    last_version_check,
    NOW() - last_version_check as days_since_check
FROM drugs 
WHERE version_check_enabled = true
AND (last_version_check IS NULL OR last_version_check < NOW() - INTERVAL '7 days')
ORDER BY last_version_check NULLS FIRST;
```

### Query 2: Version History Report
```sql
-- Last 30 days of version changes
SELECT 
    d.drug_name,
    v.old_version,
    v.new_version,
    v.publish_date,
    v.detected_at,
    v.s3_key,
    v.processed
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
WHERE v.detected_at >= NOW() - INTERVAL '30 days'
ORDER BY v.detected_at DESC;
```

### Query 3: Version Change Frequency
```sql
-- How often each drug updates
SELECT 
    d.drug_name,
    COUNT(*) as version_count,
    MIN(v.detected_at) as first_change,
    MAX(v.detected_at) as latest_change,
    MAX(v.detected_at) - MIN(v.detected_at) as time_span
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
GROUP BY d.drug_name
ORDER BY version_count DESC;
```

### Query 4: Unprocessed Version Updates
```sql
-- New versions that haven't been processed yet
SELECT 
    d.drug_name,
    v.new_version,
    v.detected_at,
    v.s3_key
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
WHERE v.processed = false
ORDER BY v.detected_at;
```

### Query 5: Enable High-Priority Drugs
```sql
-- Enable monitoring for specific drug list
UPDATE drugs 
SET version_check_enabled = true
WHERE drug_name IN (
    'SAXENDA',
    'OZEMPIC', 
    'WEGOVY',
    'MOUNJARO',
    'TRULICITY'
);

-- Verify
SELECT drug_name, set_id, version_check_enabled 
FROM drugs 
WHERE drug_name IN ('SAXENDA', 'OZEMPIC', 'WEGOVY', 'MOUNJARO', 'TRULICITY');
```

### Query 6: Bulk Enable by Category
```sql
-- Enable all GLP-1 drugs (example)
UPDATE drugs 
SET version_check_enabled = true
WHERE drug_name LIKE '%GLP%' 
OR drug_name IN (
    'SAXENDA', 'OZEMPIC', 'WEGOVY', 'VICTOZA', 
    'MOUNJARO', 'TRULICITY', 'RYBELSUS'
);
```

### Query 7: Disable Inactive Drugs
```sql
-- Disable drugs not checked in 90 days
UPDATE drugs 
SET version_check_enabled = false
WHERE version_check_enabled = true
AND last_version_check < NOW() - INTERVAL '90 days';
```

### Query 8: Check S3 Storage Paths
```sql
-- Get all S3 keys for a specific drug
SELECT 
    v.new_version,
    v.s3_key,
    v.detected_at
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
WHERE d.set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15'
ORDER BY v.detected_at DESC;
```

---

## 🔬 Advanced Testing Scenarios

### Scenario 1: Force New Version Detection
**Goal:** Test pipeline with simulated new version

```sql
-- Temporarily set old version to trigger detection
UPDATE drugs 
SET current_label_version = '1'
WHERE set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15';

-- Run manual workflow with force_download=true

-- After test, restore actual version
UPDATE drugs 
SET current_label_version = '8'
WHERE set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15';
```

### Scenario 2: Test Error Handling
**Goal:** Verify error notifications work

```sql
-- Use invalid SET_ID to trigger error
UPDATE drugs 
SET set_id = 'invalid-set-id-12345',
    version_check_enabled = true
WHERE id = 999;  -- Non-production drug

-- Run manual workflow
-- Expected: Error notification sent, workflow doesn't crash
```

### Scenario 3: Test Multiple Drugs
**Goal:** Verify batch processing

```sql
-- Enable 5 drugs
UPDATE drugs 
SET version_check_enabled = true
WHERE id IN (1, 2, 3, 4, 5);

-- Run manual workflow
-- Expected: All 5 drugs checked in sequence
```

### Scenario 4: Test S3 Archive
**Goal:** Verify old versions archived

```sql
-- Check how many versions exist for a drug
SELECT 
    d.drug_name,
    COUNT(*) as version_count
FROM drug_version_history v
JOIN drugs d ON v.drug_id = d.id
WHERE d.set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15'
GROUP BY d.drug_name;

-- If > 5, check S3 for archived versions
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "No drugs to check"
**Diagnosis:**
```sql
SELECT COUNT(*) FROM drugs WHERE version_check_enabled = true;
-- Returns: 0
```

**Solution:**
```sql
UPDATE drugs 
SET version_check_enabled = true
WHERE set_id = 'your-set-id';
```

---

### Issue 2: "Database connection failed"
**Diagnosis:**
Check DATABASE_URL format in GitHub Secrets

**Solution:**
```
Correct format: postgresql://username:password@host:5432/database
Wrong format:   postgres://... (missing 'ql')
Wrong format:   postgresql://host/database (missing credentials)
```

---

### Issue 3: "S3 access denied"
**Diagnosis:**
```bash
aws s3 ls s3://your-bucket-name/
# Returns: Access Denied
```

**Solution:**
Check IAM permissions include:
- `s3:PutObject`
- `s3:GetObject`
- `s3:ListBucket`

---

### Issue 4: "DailyMed API timeout"
**Diagnosis:**
Workflow logs show:
```
Checking: DRUG_NAME...
(hangs for 30+ seconds)
Error: Request timeout
```

**Solution:**
- This is normal for large labels
- Workflow has 30-minute timeout
- Consider increasing httpx timeout in version_checker.py

---

### Issue 5: "Slack notification not sent"
**Diagnosis:**
```
⚠️  Slack notification failed: 400
```

**Solution:**
Test webhook:
```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
-H 'Content-type: application/json' \
-d '{"text":"Test"}'
```

If returns "invalid_payload", check webhook URL is correct

---

## 📈 Success Metrics

After 1 week of operation, verify:

- [ ] At least 7 successful daily runs
- [ ] All enabled drugs checked
- [ ] Database `last_version_check` updated daily
- [ ] No persistent errors in logs
- [ ] Notifications received (if new versions)
- [ ] S3 storage costs < $1
- [ ] GitHub Actions usage < 100 minutes

---

## 🎯 Performance Benchmarks

**Expected timing (per drug):**
- Version check: 2-5 seconds
- ZIP download: 10-30 seconds (depends on label size)
- S3 upload: 5-15 seconds
- Database update: 1-2 seconds
- **Total per drug: 20-60 seconds**

**For 10 enabled drugs:**
- Sequential processing: 5-10 minutes
- With errors/retries: 10-15 minutes

---

## ✅ Go-Live Checklist

Before enabling for all drugs:

- [ ] Test run with 1 drug successful
- [ ] Test run with 5 drugs successful
- [ ] Error handling verified (invalid SET_ID test)
- [ ] Notifications working (Slack/Email)
- [ ] Database queries returning expected data
- [ ] S3 files accessible and valid
- [ ] Logs reviewed for warnings
- [ ] Cost monitoring in place
- [ ] Documentation updated
- [ ] Team trained on troubleshooting

**Ready to scale!** 🚀

---

**Next: Enable all priority drugs and monitor for 1 week**
