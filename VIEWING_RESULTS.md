# GitHub Actions Results - How to View Them

## Current State: UI Triggers, GitHub Actions Runs

### What Happens Now

```
┌─────────────────────────────────────────────────────────────┐
│  1. YOU: Click "Run Workflow" in UI                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│  2. UI: Shows "Workflow triggered" + GitHub Actions link    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│  3. GITHUB ACTIONS: Runs automation in the background       │
│     • Checks FDA DailyMed API                               │
│     • Downloads labels if version changed                   │
│     • Uploads to S3                                         │
│     • Updates database                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│  4. RESULTS: Stored in database & S3 (NOT shown in UI yet)  │
└─────────────────────────────────────────────────────────────┘
```

## ❌ Current Limitation

**The UI does NOT automatically show the results from GitHub Actions.**

After clicking "Run Workflow", you see:
- ✅ "Workflow triggered successfully"
- 🔗 Link to GitHub Actions page

But you do NOT see in the UI:
- ❌ Whether workflow succeeded or failed
- ❌ If a new version was found
- ❌ Download/upload status
- ❌ What changed in the label

## ✅ How to View Results (3 Ways)

### **Method 1: GitHub Actions Page (Real-time)** 🔴 LIVE

**Best for:** Watching the automation run in real-time

1. Click "Run Workflow" in UI
2. Copy the GitHub Actions URL from the popup
3. Open: https://github.com/Nihith132/GLP-1-platform/actions/workflows/watchdog-manual.yml
4. You'll see all running/completed workflows

**What you can see:**
```
┌────────────────────────────────────────────────────────┐
│  Workflow Runs                                         │
├────────────────────────────────────────────────────────┤
│  🟡 Manual Version Check - Ozempic     Running (2m)    │
│  ✅ Manual Version Check - Wegovy      Success (3m)    │
│  ❌ Manual Version Check - Saxenda     Failed (1m)     │
└────────────────────────────────────────────────────────┘
```

**Click on any run to see:**
- ✅ Step-by-step execution logs
- 📊 Version comparison results
- 📥 Download status
- ☁️ S3 upload confirmation
- 💾 Database update status
- ❌ Error messages if failed

### **Method 2: Dashboard (After Completion)** 📊

**Best for:** Seeing the updated versions

1. Wait for GitHub Actions to complete (2-5 minutes)
2. Go to: http://localhost:3001/dashboard
3. Refresh the page
4. You'll see updated version numbers for drugs that changed

**Example:**
```
Before workflow:
┌─────────────────────────────────┐
│  Ozempic - Version 12           │
└─────────────────────────────────┘

After workflow (if update found):
┌─────────────────────────────────┐
│  Ozempic - Version 13  ⬆️       │
└─────────────────────────────────┘
```

### **Method 3: Database Query** 💾

**Best for:** Checking exact data

```bash
# Query the database to see updated versions
psql $DATABASE_URL -c "SELECT name, version, updated_at FROM drug_labels WHERE name = 'Ozempic';"
```

**Result:**
```
    name    | version |      updated_at
------------+---------+---------------------
 Ozempic    |      13 | 2026-01-07 14:30:00
```

## 📧 Workflow Completion Notifications

The GitHub Actions workflow can send notifications when complete:

### Email Notifications (if configured)
```
Subject: ✅ Version Check Complete - Ozempic

A new version of Ozempic was found!
- Old Version: 12
- New Version: 13
- Changes: Updated safety information

S3 URL: s3://glp1-raw-labels/ozempic/v13.zip
```

### Slack Notifications (if configured)
```
🔔 Version Check Alert

Drug: Ozempic
Status: ✅ Update Found
Version: 12 → 13
Download: ✅ Complete
S3 Upload: ✅ Complete
Database: ✅ Updated
```

## 🔄 How Results Are Stored

When GitHub Actions completes, it updates:

### 1. **Database (drug_labels table)**
```sql
UPDATE drug_labels
SET 
  version = 13,           -- New version
  updated_at = NOW(),     -- Timestamp
  s3_url = 's3://...'     -- S3 location
WHERE set_id = 'abc-123';
```

### 2. **S3 Bucket**
```
s3://glp1-raw-labels/
  └── ozempic/
      ├── v12.zip  (old)
      └── v13.zip  (new) ← Downloaded by workflow
```

### 3. **GitHub Actions Logs**
```
Step 1: Check Version ✅
  Current: 12
  Latest: 13
  Status: Update available

Step 2: Download Label ✅
  URL: https://dailymed.nlm.nih.gov/...
  Size: 2.3 MB
  
Step 3: Upload to S3 ✅
  Bucket: glp1-raw-labels
  Key: ozempic/v13.zip
  
Step 4: Update Database ✅
  Table: drug_labels
  Drug: Ozempic
  New Version: 13
```

## 💡 Recommended Workflow

### For Testing (Small Scale)
1. ✅ Select 1-2 drugs in UI
2. ✅ Click "Run Workflow"
3. ✅ Open GitHub Actions link immediately
4. 👀 Watch the workflow run in real-time
5. ✅ Check logs for success/failure
6. 🔄 Refresh Dashboard to see version updates

### For Production (Bulk Checks)
1. ✅ Select multiple drugs (or all)
2. ✅ Click "Run Workflow"
3. ⏰ Wait 5-10 minutes for all to complete
4. 📊 Check Dashboard for version updates
5. 📧 Review email notifications (if configured)
6. 🗂️ Verify S3 bucket has new files

## 🚀 Future Enhancement Ideas

### Option A: Poll for Results in UI
```typescript
// After triggering workflow
pollForResults(selectedDrugs, 30000); // Poll every 30 seconds

function pollForResults(drugIds, interval) {
  const timer = setInterval(async () => {
    const updatedDrugs = await drugService.getAllDrugs();
    // Check if versions changed
    // Update UI with new versions
    // Stop polling when all complete
  }, interval);
}
```

### Option B: WebSocket Updates from Workflow
```yaml
# In workflow
- name: Send Progress Update
  run: |
    curl -X POST $BACKEND_URL/api/watchdog/progress \
      -d '{"drug_id": 1, "status": "completed", "version": 13}'
```

### Option C: Refresh Button
```tsx
<Button onClick={refreshResults}>
  🔄 Refresh Results
</Button>

// Fetches latest drug data from database
```

## ✅ Summary: Where to Check Results

| Location | What You See | When Available | Best For |
|----------|--------------|----------------|----------|
| **GitHub Actions** | Step-by-step logs, errors | Real-time | Debugging, monitoring |
| **Dashboard** | Updated versions | After completion | Quick overview |
| **Database** | Exact data | After completion | Verification |
| **S3 Bucket** | Downloaded files | After completion | File access |
| **Email** | Summary report | After completion | Notifications |

## 🎯 Quick Answer to Your Question

> "Won't the result from GitHub Actions reflect on the UI?"

**Current Answer**: No, not automatically in real-time.

**What happens:**
1. ✅ UI triggers the workflow
2. ✅ Workflow runs on GitHub Actions (2-5 min)
3. ✅ Results stored in database & S3
4. ❌ UI does NOT automatically update
5. ✅ You must manually check:
   - GitHub Actions page (for logs)
   - Dashboard (for version changes - requires refresh)
   - Database (for exact data)

**To see results:**
- **Immediately**: Open the GitHub Actions link from the popup
- **After 5 minutes**: Refresh the Dashboard to see version updates
- **For details**: Check GitHub Actions workflow logs

**The system works correctly - it just doesn't show live results in the UI yet!**
