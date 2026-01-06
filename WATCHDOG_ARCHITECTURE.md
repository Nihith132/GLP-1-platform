# Watchdog Pipeline Architecture

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GITHUB ACTIONS (Scheduler)                       │
│                                                                       │
│  ⏰ Cron: Daily at 2 AM UTC                                          │
│  🔘 Manual: On-demand trigger                                        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │   1️⃣  FETCH ENABLED DRUGS                 │
        │                                            │
        │   SELECT * FROM drugs                      │
        │   WHERE version_check_enabled = true       │
        │                                            │
        │   Result: List of SET_IDs to check        │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │   2️⃣  CHECK DAILYMED API                  │
        │                                            │
        │   For each drug:                          │
        │   GET /spls/{SET_ID}.json                 │
        │                                            │
        │   Compare: current_version vs new_version │
        │                                            │
        │   ✅ Up to date → Skip                    │
        │   🆕 New version → Continue               │
        │   ❌ Error → Log & notify                 │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │   3️⃣  DOWNLOAD NEW LABELS                 │
        │                                            │
        │   GET /spls/{SET_ID}/media.zip            │
        │                                            │
        │   Save to: /tmp/watchdog_downloads/       │
        │   Validate: Check if valid ZIP            │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │   4️⃣  UPLOAD TO AWS S3                    │
        │                                            │
        │   Path: labels/active/{SET_ID}/v{VERSION}/│
        │   File: {SET_ID}_v{VERSION}_{timestamp}.zip│
        │                                            │
        │   Metadata: drug_id, version, upload_date │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │   5️⃣  UPDATE DATABASE                     │
        │                                            │
        │   UPDATE drugs                            │
        │   SET current_label_version = new_version │
        │                                            │
        │   INSERT INTO drug_version_history        │
        │   (drug_id, old_version, new_version,     │
        │    s3_key, detected_at)                   │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │   6️⃣  SEND NOTIFICATIONS                  │
        │                                            │
        │   Slack Webhook:                          │
        │   POST to webhook URL with summary        │
        │                                            │
        │   SendGrid Email:                         │
        │   POST to /v3/mail/send                   │
        │                                            │
        │   Content: New versions, errors, summary  │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │   7️⃣  UPLOAD LOGS TO GITHUB               │
        │                                            │
        │   Store as artifact (90 days retention)   │
        │   Viewable in GitHub Actions UI           │
        └───────────────────────────────────────────┘
```

---

## 📊 Data Flow

```
┌──────────────┐
│   DailyMed   │  ← API calls (version check, download ZIP)
│     API      │
└──────┬───────┘
       │
       │ ZIP file
       ▼
┌──────────────┐
│  GitHub      │  ← Temp storage during workflow
│  Actions     │
│  Runner      │
└──────┬───────┘
       │
       │ Upload ZIP
       ▼
┌──────────────┐
│   AWS S3     │  ← Permanent storage
│   Bucket     │     labels/active/{SET_ID}/v{VERSION}/
└──────────────┘

┌──────────────┐
│  PostgreSQL  │  ← Version tracking
│  Database    │     - drugs table (current_version)
│              │     - drug_version_history table
└──────────────┘

┌──────────────┐
│    Slack     │  ← Notifications
│   Webhook    │
└──────────────┘

┌──────────────┐
│  SendGrid    │  ← Email alerts
│   Email      │
└──────────────┘
```

---

## 🗂️ Database Schema

```sql
-- Drugs table (modified)
┌─────────────────────────────────────────────┐
│              drugs                          │
├─────────────────────────────────────────────┤
│ id                    SERIAL PRIMARY KEY    │
│ drug_name             VARCHAR(255)          │
│ set_id                VARCHAR(100) UNIQUE   │
│ current_label_version VARCHAR(50)      ← NEW│
│ version_check_enabled BOOLEAN          ← NEW│
│ last_version_check    TIMESTAMP        ← NEW│
│ ... (other columns)                         │
└─────────────────────────────────────────────┘

-- Version history table (new)
┌─────────────────────────────────────────────┐
│         drug_version_history                │
├─────────────────────────────────────────────┤
│ id                SERIAL PRIMARY KEY        │
│ drug_id           INTEGER → drugs(id)       │
│ old_version       VARCHAR(50)               │
│ new_version       VARCHAR(50) NOT NULL      │
│ s3_key            VARCHAR(500)              │
│ publish_date      VARCHAR(50)               │
│ detected_at       TIMESTAMP NOT NULL        │
│ processed         BOOLEAN                   │
│ notes             TEXT                      │
└─────────────────────────────────────────────┘
```

---

## 🔐 Secrets Flow

```
GitHub Repository Secrets
├── DATABASE_URL ──────────────┐
│                               │
├── AWS_ACCESS_KEY_ID ─────────┤
├── AWS_SECRET_ACCESS_KEY ─────┼──► Injected as
├── AWS_REGION ────────────────┤    environment variables
├── S3_BUCKET_NAME ────────────┤    in GitHub Actions workflow
│                               │
├── SLACK_WEBHOOK_URL ─────────┤
├── SENDGRID_API_KEY ──────────┤
└── NOTIFICATION_EMAILS ───────┘
                                │
                                ▼
                    Python scripts access via
                        os.getenv('SECRET_NAME')
```

---

## ⏱️ Timing & Schedule

```
Time Zone Conversions (Daily 2 AM UTC):

UTC:  02:00 ─────────┐
                     │
IST:  07:30 ←────────┤ (UTC + 5:30)
PST:  18:00 ←────────┤ (UTC - 8:00)
EST:  21:00 ←────────┘ (UTC - 5:00)

Execution Timeline (typical run):
├─ 00:00  Workflow triggered
├─ 00:05  Setup Python environment
├─ 00:10  Install dependencies
├─ 00:15  Fetch enabled drugs (3 drugs)
├─ 00:45  Check DailyMed API (10s per drug)
├─ 02:30  Download ZIPs (if new versions)
├─ 03:45  Upload to S3
├─ 04:00  Update database
├─ 04:05  Send notifications
└─ 04:10  Complete (Total: ~4 minutes)
```

---

## 🎯 Decision Tree

```
                    Start Workflow
                          │
                          ▼
              Are there enabled drugs?
                    ┌─────┴─────┐
                  Yes           No
                    │             │
                    ▼             ▼
            Check DailyMed    Exit (nothing to do)
                    │
                    ▼
        Is version different?
          ┌─────────┴─────────┐
         Yes                  No
          │                    │
          ▼                    ▼
    Download ZIP         Log "up to date"
          │                    │
          ▼                    │
    Is download OK?            │
    ┌─────┴─────┐              │
   Yes          No             │
    │            │              │
    ▼            ▼              │
Upload S3    Log error          │
    │            │              │
    ▼            │              │
Update DB        │              │
    │            │              │
    └────────┬───┴──────────────┘
             │
             ▼
     Send notifications
             │
             ▼
     Upload logs & finish
```

---

## 🚦 Status Codes

```
✅ SUCCESS STATES:
├─ "new_version"    → New version detected & processed
├─ "up_to_date"     → Current version matches DailyMed
└─ "processed"      → ZIP downloaded, uploaded, DB updated

❌ ERROR STATES:
├─ "api_error"      → DailyMed API returned error
├─ "download_error" → ZIP download failed
├─ "s3_error"       → S3 upload failed
├─ "db_error"       → Database update failed
└─ "fatal_error"    → Unexpected exception

⚠️  WARNING STATES:
├─ "no_drugs"       → No drugs enabled for checking
├─ "no_version"     → DailyMed response missing version
└─ "invalid_zip"    → Downloaded file not valid ZIP
```

---

## 📦 Component Interaction

```
┌──────────────────────────────────────────────────┐
│           run_watchdog.py (Entry Point)          │
│  - Parse arguments (mode: daily/manual)          │
│  - Orchestrate workflow                          │
│  - Handle errors & logging                       │
└────────┬─────────────────────────────────────────┘
         │
         ├──────────────────────┬───────────────────┬──────────────────┐
         │                      │                   │                  │
         ▼                      ▼                   ▼                  ▼
┌─────────────────┐   ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ VersionChecker  │   │   S3Uploader    │  │   Notifier   │  │   Database   │
├─────────────────┤   ├─────────────────┤  ├──────────────┤  ├──────────────┤
│ - get_enabled   │   │ - upload_label  │  │ - send_slack │  │ AsyncSession │
│ - check_version │   │ - archive_old   │  │ - send_email │  │              │
│ - download_zip  │   │ - upload_log    │  │ - send_error │  │ SQLAlchemy   │
│ - save_update   │   │                 │  │              │  │ async/await  │
└─────────────────┘   └─────────────────┘  └──────────────┘  └──────────────┘
         │                      │                   │                  │
         └──────────────────────┴───────────────────┴──────────────────┘
                                │
                                ▼
                        🎉 Complete Pipeline
```

---

## 🔄 Version Lifecycle

```
1. Initial State
   drugs.current_label_version = "8"
   drugs.version_check_enabled = true

2. Watchdog Detects Change
   DailyMed reports version "9"
   
3. Download & Upload
   ├─ Download: {SET_ID}_v9.zip
   ├─ Upload S3: labels/active/{SET_ID}/v9/...
   └─ Archive old: labels/active/{SET_ID}/v8/ → labels/archive/...

4. Database Update
   ├─ UPDATE drugs SET current_label_version = "9"
   └─ INSERT INTO drug_version_history (old: "8", new: "9")

5. Notification Sent
   ├─ Slack: "🆕 SAXENDA: 8 → 9"
   └─ Email: "Watchdog Report: 1 New Version(s)"

6. Future Checks
   Next run: version "9" == "9" → No action needed
```

---

## 💡 Key Features

- ✅ **Automated**: Runs daily without manual intervention
- ✅ **Scalable**: Add unlimited drugs to monitoring
- ✅ **Reliable**: Error handling + retry logic
- ✅ **Observable**: Logs, notifications, database history
- ✅ **Cost-effective**: ~$2-5/month for typical usage
- ✅ **Secure**: Secrets managed via GitHub
- ✅ **Flexible**: Manual trigger available anytime
- ✅ **Archived**: 90-day log retention + S3 backups

---

**For implementation steps, see: `WATCHDOG_SETUP_GUIDE.md`**
