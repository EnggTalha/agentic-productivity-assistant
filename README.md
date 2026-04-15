# 🧑‍💼 Personal AI Chief of Staff

> Connects to your Gmail and Google Calendar. Every morning it reads your emails, schedules your day, prioritizes tasks, drafts replies, and delivers a briefing to Slack — all autonomously.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Claude](https://img.shields.io/badge/Powered%20by-Claude%20Opus-blueviolet?logo=anthropic)
![Gmail](https://img.shields.io/badge/Gmail-API-red?logo=gmail)
![Google Calendar](https://img.shields.io/badge/Google%20Calendar-API-blue?logo=googlecalendar)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 Demo

```
╭──────────────────────────────────────────────────────────────╮
│  Personal AI Chief of Staff                                  │
│  Agent for: Talha (Software Engineer)                        │
│  Mode: DRY RUN | TZ: Asia/Karachi                           │
╰──────────────────────────────────────────────────────────────╯

📬 Fetching emails...
✓ Fetched 5 emails.

📅 Fetching calendar...
✓ Fetched 4 calendar events.

🧠 Triaging emails...
  ✓ Triaged 5 emails.

✅ Extracting tasks...
  ✓ Extracted 7 tasks.

📋 Generating morning brief...

╭──────────────────────────────────────────────────────────────╮
│  Good morning, Talha! Big day ahead — 4 meetings, 2 urgent  │
│  items, and an interview to wrap up. Let's get after it.    │
╰──────────────────────────────────────────────────────────────╯

📅 Schedule
  10:00 AM  Daily Standup          ali, zara, hamza...
  11:00 AM  Sprint Planning        team@company.com
  02:00 PM  1:1 with Sarah         sarah@company.com
  04:00 PM  Interview — Farhan K.  hr, farhan.k

✅ Priority Tasks
  🔴  Submit interview feedback for Farhan K.         due: 3:00 PM
  🔴  Complete Q2 self-assessment form                due: Friday EOD
  🟠  Process Invoice #4521 payment ($450)            due: Apr 19
  🟡  Prepare talking points for 1:1 with Sarah       today
  🟢  Review standup notes — Ali blocked on DB creds  this week

📬 Email Actions
  ✉️ reply   Sarah Manager      Q2 Performance Review — Action Required   U
  🚩 flag    HR Team             Interview feedback needed — Farhan K.     U
  📦 archive Slack Bot           Team standup notes — April 16             N
  📦 archive TechBrief           Weekly newsletter: AI tools roundup       L

⏰ Focus Block: 12:00–1:30 PM between sprint planning and your 1:1

👀 Watch Out For
  • Interview feedback deadline is 3 PM — don't miss it
  • Ali is blocked on DB creds — may need your help

⚡ Quick Wins
  • Mark standup notes as read
  • Forward invoice #4521 to accounts
  • Check if DB creds issue is in your scope

✓ Chief of Staff run complete!
```

---

## 🧠 How It Works

```
┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐
│  1. FETCH    │──▶│  2. FETCH    │──▶│  3. TRIAGE (Claude)     │
│              │   │              │   │                         │
│  Gmail API   │   │  Google Cal  │   │  Reads all emails       │
│  Last 24h    │   │  Today's     │   │  Decides: reply/flag/   │
│  Unread +    │   │  events      │   │  archive/ignore         │
│  Important   │   │              │   │  Drafts replies         │
└──────────────┘   └──────────────┘   └─────────────────────────┘
                                                  │
                                                  ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐
│  6. DELIVER  │◀──│  5. APPLY    │◀──│  4. SYNTHESIZE (Claude) │
│              │   │              │   │                         │
│  Slack brief │   │  Create      │   │  Extract tasks          │
│  Markdown    │   │  Gmail drafts│   │  Prioritize day         │
│  file saved  │   │  Archive     │   │  Generate brief         │
│  Terminal    │   │  emails      │   │  Find focus block       │
└──────────────┘   └──────────────┘   └─────────────────────────┘
```

---

## ✨ Features

| Feature | Details |
|---|---|
| 📬 Email triage | Claude reads every email and decides: reply, flag, archive, or ignore |
| ✉️ Draft replies | Auto-drafts professional replies saved to Gmail Drafts |
| 📅 Calendar sync | Pulls today's full schedule with attendees |
| ✅ Task extraction | Infers action items from emails and meetings |
| 📋 Morning brief | Personalized daily briefing with schedule, tasks, and email actions |
| 💬 Slack delivery | Posts formatted brief to any Slack channel |
| ⏰ Focus block | Recommends best deep-work window based on your calendar |
| ⚡ Quick wins | Surfaces tasks completable in under 5 minutes |
| 💾 Local archive | Every brief saved as Markdown + JSON |
| ⏱️ Schedulable | Run via cron, Task Scheduler, or GitHub Actions |

---

## 🗂️ Project Structure

```
chief-of-staff/
├── main.py                      # CLI entry point
├── config.py                    # Config, env vars, Pydantic models
├── requirements.txt
├── .env.example
├── SETUP.md                     # Google OAuth setup guide
│
├── agent/
│   ├── brain.py                 # Claude: email triage, tasks, brief
│   └── orchestrator.py          # Main agentic loop
│
├── tools/
│   ├── gmail_tool.py            # Gmail API: read, draft, archive
│   ├── calendar_tool.py         # Google Calendar API: read, create
│   ├── slack_tool.py            # Slack: deliver brief
│   └── reporter.py              # Terminal + Markdown brief printer
│
└── data/
    ├── briefs/                  # Saved daily briefs (auto-generated)
    ├── emails/                  # Email cache
    └── google_token.json        # OAuth token (auto-generated on first run)
```

---

## 🚀 Quickstart

### 1. Clone & install

```bash
git clone https://github.com/yourusername/personal-ai-chief-of-staff.git
cd personal-ai-chief-of-staff

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Fill in `.env`:
- `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com)
- `YOUR_NAME`, `YOUR_EMAIL`, `YOUR_ROLE`
- Google credentials (see **SETUP.md** — takes 5 minutes)

### 3. Set up Google API

Follow [SETUP.md](SETUP.md) to get your Gmail + Calendar credentials. Takes about 5 minutes.

### 4. Run dry run first (safe — no emails sent)

```bash
python main.py --dry-run
```

### 5. Go live

```bash
python main.py --live
```

---

## ⚙️ CLI Reference

```
python main.py [OPTIONS]

Options:
  --dry-run        Simulate — no emails sent, no Slack messages (default)
  --live           Actually create drafts and post to Slack
  --schedule       Daemon mode — runs daily at BRIEF_HOUR in .env
  --emails-only    Only triage emails, skip brief generation
  --brief-only     Generate brief without applying email actions

Examples:
  python main.py --dry-run           # safe test
  python main.py --live              # full live run
  python main.py --schedule --live   # run every morning automatically
```

---

## 🔑 API Keys & Cost

| Service | Used For | Cost |
|---|---|---|
| Anthropic Claude | Email triage, task extraction, brief | ~$0.05–0.15 per run |
| Gmail API | Read emails, create drafts | Free (Google) |
| Google Calendar API | Read events, create events | Free (Google) |
| Slack API | Deliver morning brief | Free (Slack) |

**Estimated cost per day:** ~$0.10

---

## 🛠️ Customization

### Change what Claude focuses on

Edit the triage prompt in `agent/brain.py` to add your rules:

```python
# Add to the triage prompt:
"Always flag emails from my CEO (ceo@company.com) as urgent.
Never draft replies to newsletters.
If an email contains an invoice, always flag it as high priority."
```

### Add more integrations

The modular `tools/` folder makes it easy to add:
- **Notion** — sync tasks to a Notion database
- **WhatsApp** — deliver brief via WhatsApp (Twilio)
- **Telegram** — deliver via Telegram Bot API
- **Linear / Jira** — pull in ticket updates

---

## 🤝 Contributing

Ideas welcome:
- [ ] WhatsApp delivery via Twilio
- [ ] Notion task sync
- [ ] Follow-up tracker (did you get a reply?)
- [ ] Weekly summary mode
- [ ] Meeting prep notes (research attendees before 1:1s)
- [ ] Voice brief via text-to-speech

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 🙋 Author

Built by [Your Name](https://github.com/yourusername)

> ⭐ Star this repo if it made your mornings smoother!
