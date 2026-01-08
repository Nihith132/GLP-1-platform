# GitHub Actions Integration Setup

This document explains how to set up GitHub Actions integration for the Version Checker feature.

## Overview

When you click "Run Workflow" in the Version Checker page, it triggers the GitHub Actions workflow `watchdog-manual.yml` which:
1. Checks FDA DailyMed for label version updates
2. Downloads new versions if available
3. Uploads to S3
4. Updates the database
5. Sends notifications

## Setup Steps

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Direct link: https://github.com/settings/tokens

2. Click **"Generate new token (classic)"**

3. Configure the token:
   - **Note**: "GLP-1 Platform Workflow Trigger"
   - **Expiration**: Choose your preferred expiration (recommend 90 days or No expiration)
   - **Scopes**: Select the following:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)

4. Click **"Generate token"**

5. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

### 2. Add Token to Environment Variables

1. Open the `.env` file in the project root

2. Find the GitHub Actions section and add your token:
   ```env
   # ===== GitHub Actions Integration =====
   GITHUB_TOKEN=ghp_your_token_here_xxxxxxxxxxxxxxxxxx
   GITHUB_REPO_OWNER=Nihith132
   GITHUB_REPO_NAME=GLP-1-platform
   ```

3. Make sure `.env` is in `.gitignore` (it should be by default)

### 3. Restart Backend Server

After adding the token, restart your backend server:

```bash
cd backend
uvicorn api.main:app --reload
```

## How It Works

### Frontend Flow
1. User selects drugs in Version Checker page
2. Clicks "Run Workflow" button
3. Frontend calls `/api/watchdog/trigger` with drug IDs

### Backend Flow
1. Backend receives drug IDs
2. Queries database for SET_IDs
3. Calls GitHub API to trigger `watchdog-manual.yml` workflow
4. Returns success message with GitHub Actions URL

### GitHub Actions Flow
1. Workflow runs in GitHub infrastructure
2. Sets up Python environment
3. Runs `scripts/run_watchdog.py`
4. Checks FDA API, downloads labels, uploads to S3
5. Updates database
6. Sends notifications

## Viewing Workflow Runs

After triggering a workflow, you can view its progress:

1. Go to: https://github.com/Nihith132/GLP-1-platform/actions/workflows/watchdog-manual.yml

2. You'll see all workflow runs with:
   - Status (queued, in progress, completed, failed)
   - Drug being checked
   - Start time and duration
   - Logs and artifacts

## Troubleshooting

### "GITHUB_TOKEN not configured" Error
- Make sure you've added `GITHUB_TOKEN` to `.env`
- Restart the backend server after adding it

### "GitHub API returned 401" Error
- Your token may have expired
- Generate a new token and update `.env`

### "GitHub API returned 404" Error
- Check that `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` are correct
- Make sure your token has `repo` and `workflow` scopes

### Workflow Not Appearing in GitHub Actions
- Wait a few seconds - GitHub API returns 204 immediately but workflow may take 5-10 seconds to appear
- Check the Actions tab in GitHub to confirm

## API Response Example

Successful trigger:
```json
{
  "status": "success",
  "message": "GitHub Actions workflows triggered successfully",
  "drug_count": 1,
  "drugs": [
    {
      "id": 7,
      "name": "Ozempic",
      "set_id": "2160dee6-dc44-4639-af3f-fd1ac2a32d15"
    }
  ],
  "workflow_url": "https://github.com/Nihith132/GLP-1-platform/actions/workflows/watchdog-manual.yml"
}
```

## Security Notes

- Never commit your GitHub token to version control
- Use token expiration for better security
- Rotate tokens periodically
- Only grant minimum required scopes
- If token is compromised, revoke it immediately in GitHub settings
