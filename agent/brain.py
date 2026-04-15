"""
agent/brain.py — Claude-powered intelligence for the Chief of Staff agent.
Handles: email triage, task extraction, brief generation, reply drafting.
"""

from __future__ import annotations
import json
from datetime import datetime
from typing import List, Optional
import anthropic
from rich.console import Console
import pytz

from config import (
    EnvConfig, EmailMessage, EmailAction, CalendarEvent,
    Task, DailyBrief
)

console = Console()
_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=EnvConfig.ANTHROPIC_API_KEY)
    return _client


# ── Email triage ───────────────────────────────────────────────────────

def triage_emails(emails: List[EmailMessage]) -> List[EmailAction]:
    """
    Claude reads all emails and decides: reply / archive / flag / ignore.
    For emails needing a reply, it drafts one.
    """
    console.print(f"  [dim]Triaging {len(emails)} emails...[/dim]")

    email_summaries = "\n\n".join([
        f"ID: {e.id}\nFrom: {e.sender} <{e.sender_email}>\nSubject: {e.subject}\nDate: {e.date}\nBody: {e.body[:500]}"
        for e in emails
    ])

    prompt = f"""You are {EnvConfig.YOUR_NAME}'s personal chief of staff. Triage these emails intelligently.

YOUR PROFILE:
Name: {EnvConfig.YOUR_NAME}
Email: {EnvConfig.YOUR_EMAIL}
Role: {EnvConfig.YOUR_ROLE}

EMAILS TO TRIAGE:
{email_summaries}

For each email decide the best action:
- "reply": needs a response (you must write a draft_reply)
- "flag": important, needs human attention, no reply needed
- "archive": low value, can be cleaned up
- "ignore": newsletters, notifications, spam

Priority levels: urgent | high | normal | low

Respond ONLY with a JSON array (no markdown):
[
  {{
    "email_id": "...",
    "subject": "...",
    "sender": "...",
    "action": "reply|archive|flag|ignore",
    "priority": "urgent|high|normal|low",
    "draft_reply": "Full professional reply text (null if not replying)",
    "reason": "One sentence explaining the decision"
  }}
]

For draft replies: be professional, concise, and write as {EnvConfig.YOUR_NAME}.
Urgent = deadline today or blocking others. High = needs response today. Normal = respond this week."""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        actions = [EmailAction(**item) for item in data]
        console.print(f"  [green]✓[/green] Triaged {len(actions)} emails.")
        return actions
    except Exception as e:
        console.print(f"  [red]Email triage failed:[/red] {e}")
        return []


# ── Task extraction ────────────────────────────────────────────────────

def extract_tasks(
    emails: List[EmailMessage],
    events: List[CalendarEvent],
    existing_tasks: List[Task] = None,
) -> List[Task]:
    """
    Claude infers actionable tasks from emails and calendar events.
    """
    console.print("  [dim]Extracting tasks...[/dim]")

    email_context = "\n".join([
        f"- Email from {e.sender}: '{e.subject}' — {e.snippet}"
        for e in emails[:15]
    ])
    calendar_context = "\n".join([
        f"- {e.title} at {e.start} with {', '.join(e.attendees[:3]) or 'no attendees'}"
        for e in events
    ])

    prompt = f"""You are {EnvConfig.YOUR_NAME}'s chief of staff. Extract ALL actionable tasks from today's context.

TODAY'S DATE: {_today()}
TIMEZONE: {EnvConfig.TIMEZONE}

EMAILS:
{email_context}

CALENDAR:
{calendar_context}

Extract every task that {EnvConfig.YOUR_NAME} needs to do. Include:
- Explicit requests in emails
- Preparation needed for meetings
- Follow-ups implied by context
- Deadlines mentioned

Respond ONLY with a JSON array (no markdown):
[
  {{
    "id": "task_001",
    "title": "Clear action verb + what to do",
    "source": "email|calendar|inferred",
    "priority": "urgent|high|normal|low",
    "due": "HH:MM today or YYYY-MM-DD or null",
    "context": "Which email/meeting this came from"
  }}
]

Priority: urgent = due today before noon, high = due today, normal = this week, low = whenever."""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        tasks = [Task(**item) for item in data]
        console.print(f"  [green]✓[/green] Extracted {len(tasks)} tasks.")
        return tasks
    except Exception as e:
        console.print(f"  [red]Task extraction failed:[/red] {e}")
        return []


# ── Daily brief generation ─────────────────────────────────────────────

def generate_daily_brief(
    emails: List[EmailMessage],
    events: List[CalendarEvent],
    actions: List[EmailAction],
    tasks: List[Task],
) -> DailyBrief:
    """
    Claude synthesizes everything into a personalized morning brief.
    """
    console.print("  [dim]Generating daily brief...[/dim]")

    tz = pytz.timezone(EnvConfig.TIMEZONE)
    now = datetime.now(tz)
    hour = now.hour
    greeting_time = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

    schedule_text = "\n".join([f"- {e.title} at {e.start}" for e in events])
    urgent_tasks  = [t for t in tasks if t.priority in ("urgent", "high")]
    reply_actions = [a for a in actions if a.action == "reply"]
    flag_actions  = [a for a in actions if a.action == "flag"]

    prompt = f"""You are {EnvConfig.YOUR_NAME}'s brilliant personal chief of staff. Generate their morning brief.

CONTEXT:
- Name: {EnvConfig.YOUR_NAME}, Role: {EnvConfig.YOUR_ROLE}
- Date: {_today()}, Time: {now.strftime('%H:%M')} {EnvConfig.TIMEZONE}
- Unread emails: {sum(1 for e in emails if e.is_unread)}
- Meetings today: {len(events)}
- Tasks identified: {len(tasks)}
- Emails needing reply: {len(reply_actions)}

TODAY'S SCHEDULE:
{schedule_text or 'No meetings today — clear day!'}

URGENT/HIGH TASKS:
{chr(10).join([f'- {t.title} (due: {t.due or "today"})' for t in urgent_tasks]) or 'None'}

FLAGGED EMAILS:
{chr(10).join([f'- {a.subject} from {a.sender}' for a in flag_actions]) or 'None'}

Respond ONLY with a JSON object (no markdown):
{{
  "date": "{_today()}",
  "greeting": "{greeting_time}, {EnvConfig.YOUR_NAME}! [1-2 warm, energetic sentences about the day ahead]",
  "executive_summary": "3-4 sentence overview of today — what matters most, any risks, general vibe",
  "focus_block": "Recommended 90-min deep work window e.g. '11:00–12:30 AM between standup and sprint planning'",
  "quick_wins": ["task under 5 min", "another quick win", "one more"],
  "watch_out": ["potential issue or risk to be aware of today"],
  "motivational_note": "One sharp, relevant, non-generic motivational sentence tailored to today's context"
}}"""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        return DailyBrief(
            date=_today(),
            greeting=data["greeting"],
            executive_summary=data["executive_summary"],
            todays_schedule=events,
            priority_tasks=sorted(tasks, key=lambda t: {"urgent": 0, "high": 1, "normal": 2, "low": 3}.get(t.priority, 2)),
            email_actions=actions,
            focus_block=data.get("focus_block", "No specific recommendation"),
            quick_wins=data.get("quick_wins", []),
            watch_out=data.get("watch_out", []),
            motivational_note=data.get("motivational_note", "Make it count."),
        )

    except Exception as e:
        console.print(f"  [red]Brief generation failed:[/red] {e}")
        return DailyBrief(
            date=_today(),
            greeting=f"{greeting_time}, {EnvConfig.YOUR_NAME}!",
            executive_summary="Brief generation encountered an error. Check logs.",
            todays_schedule=events,
            priority_tasks=tasks,
            email_actions=actions,
            focus_block="N/A",
            quick_wins=[],
            watch_out=[str(e)],
            motivational_note="Keep going.",
        )


def _today() -> str:
    tz = pytz.timezone(EnvConfig.TIMEZONE)
    return datetime.now(tz).strftime("%A, %B %d, %Y")
