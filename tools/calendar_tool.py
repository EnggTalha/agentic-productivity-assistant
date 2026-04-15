"""
tools/calendar_tool.py — Read and create events via Google Calendar API (free).
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from rich.console import Console
import pytz

from config import EnvConfig, CalendarEvent

console = Console()

SCOPES_CAL = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def get_calendar_service():
    """Build authenticated Google Calendar service."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from pathlib import Path

        token_path = Path(EnvConfig.GOOGLE_TOKEN_PATH)
        all_scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
        ]

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), all_scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

        return build("calendar", "v3", credentials=creds) if creds else None

    except Exception as e:
        console.print(f"[red]Calendar auth error:[/red] {e}")
        return None


def fetch_todays_events() -> List[CalendarEvent]:
    """Fetch all calendar events for today."""
    service = get_calendar_service()
    if not service:
        console.print("[yellow]Calendar unavailable — using mock events.[/yellow]")
        return _mock_events()

    try:
        tz = pytz.timezone(EnvConfig.TIMEZONE)
        now = datetime.now(tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day   = now.replace(hour=23, minute=59, second=59)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for e in events_result.get("items", []):
            start = e["start"].get("dateTime", e["start"].get("date", ""))
            end   = e["end"].get("dateTime", e["end"].get("date", ""))
            attendees = [a.get("email", "") for a in e.get("attendees", [])]

            events.append(CalendarEvent(
                id=e["id"],
                title=e.get("summary", "Untitled"),
                start=start,
                end=end,
                location=e.get("location"),
                attendees=attendees,
                description=e.get("description", "")[:500],
                is_all_day="date" in e["start"],
            ))

        console.print(f"[green]✓[/green] Fetched {len(events)} calendar events.")
        return events

    except Exception as e:
        console.print(f"[red]Calendar fetch error:[/red] {e}")
        return _mock_events()


def fetch_upcoming_events(days: int = 3) -> List[CalendarEvent]:
    """Fetch events for the next N days."""
    service = get_calendar_service()
    if not service:
        return _mock_events()

    try:
        tz = pytz.timezone(EnvConfig.TIMEZONE)
        now = datetime.now(tz)
        future = now + timedelta(days=days)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=future.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        ).execute()

        events = []
        for e in events_result.get("items", []):
            start = e["start"].get("dateTime", e["start"].get("date", ""))
            end   = e["end"].get("dateTime", e["end"].get("date", ""))
            attendees = [a.get("email", "") for a in e.get("attendees", [])]

            events.append(CalendarEvent(
                id=e["id"],
                title=e.get("summary", "Untitled"),
                start=start, end=end,
                location=e.get("location"),
                attendees=attendees,
            ))

        return events

    except Exception as e:
        console.print(f"[red]Calendar fetch error:[/red] {e}")
        return []


def create_event(title: str, start: str, end: str, description: str = "") -> Optional[str]:
    """Create a new calendar event. Returns event ID."""
    if EnvConfig.DRY_RUN:
        console.print(f"  [yellow][DRY RUN][/yellow] Would create event: {title} at {start}")
        return "dry-run-event-id"

    service = get_calendar_service()
    if not service:
        return None

    try:
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": EnvConfig.TIMEZONE},
            "end":   {"dateTime": end,   "timeZone": EnvConfig.TIMEZONE},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return created.get("id")
    except Exception as e:
        console.print(f"  [red]Event creation failed:[/red] {e}")
        return None


def _mock_events() -> List[CalendarEvent]:
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        CalendarEvent(
            id="evt001", title="Daily Standup",
            start=f"{today}T10:00:00+05:00", end=f"{today}T10:15:00+05:00",
            attendees=["ali@company.com", "zara@company.com", "hamza@company.com"],
            description="Quick team sync",
        ),
        CalendarEvent(
            id="evt002", title="1:1 with Sarah (Manager)",
            start=f"{today}T14:00:00+05:00", end=f"{today}T14:30:00+05:00",
            attendees=["sarah@company.com"],
            description="Weekly sync — Q2 review discussion",
        ),
        CalendarEvent(
            id="evt003", title="System Design Interview — Farhan K.",
            start=f"{today}T16:00:00+05:00", end=f"{today}T17:00:00+05:00",
            attendees=["hr@company.com", "farhan.k@gmail.com"],
            location="Google Meet",
        ),
        CalendarEvent(
            id="evt004", title="Sprint Planning",
            start=f"{today}T11:00:00+05:00", end=f"{today}T12:00:00+05:00",
            attendees=["team@company.com"],
        ),
    ]
