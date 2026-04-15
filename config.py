"""
config.py — Central config and data models for the Personal AI Chief of Staff.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
EMAILS_DIR  = DATA_DIR / "emails"
CAL_DIR     = DATA_DIR / "calendar"
TASKS_DIR   = DATA_DIR / "tasks"
BRIEFS_DIR  = DATA_DIR / "briefs"
LOG_DIR     = BASE_DIR / "logs"

for d in [EMAILS_DIR, CAL_DIR, TASKS_DIR, BRIEFS_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Env ────────────────────────────────────────────────────────────────
class EnvConfig:
    ANTHROPIC_API_KEY: str  = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_CLIENT_ID:  str  = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_TOKEN_PATH: str  = os.getenv("GOOGLE_TOKEN_PATH", "data/google_token.json")
    SLACK_BOT_TOKEN:   str  = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL_ID:  str  = os.getenv("SLACK_CHANNEL_ID", "")
    TIMEZONE:          str  = os.getenv("TIMEZONE", "Asia/Karachi")
    MAX_EMAILS:        int  = int(os.getenv("MAX_EMAILS_TO_READ", "30"))
    MAX_DRAFTS:        int  = int(os.getenv("MAX_EMAILS_TO_DRAFT", "5"))
    DRY_RUN:           bool = os.getenv("DRY_RUN", "true").lower() == "true"
    YOUR_NAME:         str  = os.getenv("YOUR_NAME", "")
    YOUR_EMAIL:        str  = os.getenv("YOUR_EMAIL", "")
    YOUR_ROLE:         str  = os.getenv("YOUR_ROLE", "")


# ── Data Models ────────────────────────────────────────────────────────

class EmailMessage(BaseModel):
    id:          str
    thread_id:   str
    subject:     str
    sender:      str
    sender_email: str
    snippet:     str
    body:        str
    date:        str
    is_unread:   bool
    labels:      List[str] = Field(default_factory=list)


class EmailAction(BaseModel):
    email_id:    str
    subject:     str
    sender:      str
    action:      str        # "reply" | "archive" | "flag" | "delegate" | "ignore"
    priority:    str        # "urgent" | "high" | "normal" | "low"
    draft_reply: Optional[str] = None
    reason:      str


class CalendarEvent(BaseModel):
    id:          str
    title:       str
    start:       str
    end:         str
    location:    Optional[str] = None
    attendees:   List[str] = Field(default_factory=list)
    description: Optional[str] = None
    is_all_day:  bool = False


class Task(BaseModel):
    id:          str
    title:       str
    source:      str        # "email" | "calendar" | "inferred"
    priority:    str        # "urgent" | "high" | "normal" | "low"
    due:         Optional[str] = None
    context:     str        # why this task was created
    done:        bool = False


class DailyBrief(BaseModel):
    date:              str
    greeting:          str
    executive_summary: str
    todays_schedule:   List[CalendarEvent]
    priority_tasks:    List[Task]
    email_actions:     List[EmailAction]
    focus_block:       str      # recommended deep work slot
    quick_wins:        List[str]  # things you can knock out in <5 min
    watch_out:         List[str]  # potential issues / things needing attention
    motivational_note: str
