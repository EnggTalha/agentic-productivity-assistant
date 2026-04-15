# 🔑 Google API Setup Guide

Getting Gmail + Calendar access takes about **5 minutes**. Follow these steps:

---

## Step 1 — Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **"New Project"** → name it `chief-of-staff` → **Create**
3. Make sure your new project is selected in the top dropdown

---

## Step 2 — Enable APIs

1. Go to **APIs & Services → Library**
2. Search for and enable:
   - ✅ **Gmail API**
   - ✅ **Google Calendar API**

---

## Step 3 — Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click **"+ Create Credentials" → "OAuth client ID"**
3. If prompted, configure the OAuth consent screen first:
   - User type: **External**
   - App name: `Chief of Staff`
   - Add your email as a test user
4. Back in Credentials:
   - Application type: **Desktop app**
   - Name: `chief-of-staff`
   - Click **Create**
5. Copy the **Client ID** and **Client Secret**

---

## Step 4 — Add to .env

```bash
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here
```

---

## Step 5 — First Run (OAuth flow)

On your first run, a browser window will open asking you to authorize the app.
After you approve, a `data/google_token.json` file is saved — you won't need to authorize again.

```bash
python main.py --dry-run
```

---

## Slack Setup (Optional)

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App**
2. Choose **"From scratch"** → name it `Chief of Staff`
3. Go to **OAuth & Permissions** → add bot token scopes:
   - `chat:write`
   - `chat:write.public`
4. Click **Install to Workspace** → copy the **Bot User OAuth Token**
5. Add to `.env`:
   ```
   SLACK_BOT_TOKEN=xoxb-your-token-here
   SLACK_CHANNEL_ID=C0XXXXXXXXX   # Right-click channel → Copy link → last part of URL
   ```

---

## Running Daily Automatically

### Option A — Cron (Linux/Mac)
```bash
# Run at 8:00 AM every day
crontab -e
0 8 * * * cd /path/to/chief-of-staff && python main.py --live
```

### Option B — Task Scheduler (Windows)
Use Windows Task Scheduler to run `python main.py --live` at 8:00 AM daily.

### Option C — GitHub Actions (free, runs in cloud)
```yaml
# .github/workflows/daily-brief.yml
name: Daily Brief
on:
  schedule:
    - cron: '0 3 * * *'   # 8 AM PKT = 3 AM UTC
jobs:
  brief:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: python main.py --live
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_TOKEN_PATH: data/google_token.json
```
