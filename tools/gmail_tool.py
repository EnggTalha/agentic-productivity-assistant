"""
tools/gmail_tool.py — Read emails, draft replies, archive, and label via Gmail API.
Uses OAuth2 (free Google API — no paid tier needed).
"""

from __future__ import annotations
import base64
import json
import os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional
from rich.console import Console

from config import EnvConfig, EmailMessage, EMAILS_DIR

console = Console()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """Build and return authenticated Gmail service."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        token_path = Path(EnvConfig.GOOGLE_TOKEN_PATH)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Build credentials from env vars
                client_config = {
                    "installed": {
                        "client_id": EnvConfig.GOOGLE_CLIENT_ID,
                        "client_secret": EnvConfig.GOOGLE_CLIENT_SECRET,
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                creds = flow.run_local_server(port=0)

            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    except Exception as e:
        console.print(f"[red]Gmail auth error:[/red] {e}")
        return None


def fetch_recent_emails(max_results: int = 30) -> List[EmailMessage]:
    """Fetch recent unread + important emails."""
    service = get_gmail_service()
    if not service:
        console.print("[yellow]Gmail unavailable — using mock emails.[/yellow]")
        return _mock_emails()

    try:
        results = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            q="is:unread OR is:important newer_than:1d",
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()
            email = _parse_message(msg)
            if email:
                emails.append(email)

        console.print(f"[green]✓[/green] Fetched {len(emails)} emails.")
        return emails

    except Exception as e:
        console.print(f"[red]Gmail fetch error:[/red] {e}")
        return _mock_emails()


def send_draft(email_id: str, reply_body: str, to: str, subject: str) -> bool:
    """Create a draft reply to an email."""
    if EnvConfig.DRY_RUN:
        console.print(f"  [yellow][DRY RUN][/yellow] Would draft reply to {to}: {subject[:50]}")
        return True

    service = get_gmail_service()
    if not service:
        return False

    try:
        message = MIMEText(reply_body)
        message["to"] = to
        message["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        service.users().drafts().create(
            userId="me", body={"message": {"raw": raw, "threadId": email_id}}
        ).execute()
        console.print(f"  [green]✓[/green] Draft created for {to}")
        return True
    except Exception as e:
        console.print(f"  [red]Draft failed:[/red] {e}")
        return False


def archive_email(email_id: str) -> bool:
    """Archive (remove from inbox) an email."""
    if EnvConfig.DRY_RUN:
        return True
    service = get_gmail_service()
    if not service:
        return False
    try:
        service.users().messages().modify(
            userId="me", id=email_id,
            body={"removeLabelIds": ["INBOX"]}
        ).execute()
        return True
    except Exception:
        return False


def mark_read(email_id: str) -> bool:
    """Mark email as read."""
    if EnvConfig.DRY_RUN:
        return True
    service = get_gmail_service()
    if not service:
        return False
    try:
        service.users().messages().modify(
            userId="me", id=email_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        return True
    except Exception:
        return False


# ── Parsers ────────────────────────────────────────────────────────────

def _parse_message(msg: dict) -> Optional[EmailMessage]:
    try:
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender  = headers.get("From", "Unknown")
        date    = headers.get("Date", "")

        sender_email = sender
        if "<" in sender:
            sender_email = sender.split("<")[1].rstrip(">")
            sender = sender.split("<")[0].strip().strip('"')

        body = _extract_body(msg["payload"])
        labels = msg.get("labelIds", [])

        return EmailMessage(
            id=msg["id"],
            thread_id=msg["threadId"],
            subject=subject,
            sender=sender,
            sender_email=sender_email,
            snippet=msg.get("snippet", "")[:200],
            body=body[:3000],
            date=date,
            is_unread="UNREAD" in labels,
            labels=labels,
        )
    except Exception:
        return None


def _extract_body(payload: dict) -> str:
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result
    return ""


def _mock_emails() -> List[EmailMessage]:
    return [
        EmailMessage(
            id="mock001", thread_id="t001",
            subject="Q2 Performance Review — Action Required",
            sender="Sarah Manager", sender_email="sarah@company.com",
            snippet="Hi, your Q2 review is due by end of week. Please complete the self-assessment form.",
            body="Hi,\n\nYour Q2 performance review is due by Friday EOD. Please complete the self-assessment form at [link] and schedule a 1:1 with me.\n\nBest,\nSarah",
            date="Thu, 16 Apr 2026 09:00:00 +0500",
            is_unread=True, labels=["INBOX", "UNREAD", "IMPORTANT"],
        ),
        EmailMessage(
            id="mock002", thread_id="t002",
            subject="Invoice #4521 — Payment Due",
            sender="Acme Billing", sender_email="billing@acme.com",
            snippet="Your invoice of $450 is due in 3 days. Please process payment to avoid late fees.",
            body="Dear Customer,\n\nInvoice #4521 for $450.00 is due on April 19, 2026. Please process payment via your account portal.\n\nAcme Billing Team",
            date="Thu, 16 Apr 2026 08:30:00 +0500",
            is_unread=True, labels=["INBOX", "UNREAD"],
        ),
        EmailMessage(
            id="mock003", thread_id="t003",
            subject="Team standup notes — April 16",
            sender="Slack Bot", sender_email="notify@slack.com",
            snippet="3 team members posted updates in #standup channel.",
            body="Standup updates:\n- Ali: Finishing auth module, blocked on DB creds\n- Zara: Deployed v2.1 to staging\n- Hamza: OOO today",
            date="Thu, 16 Apr 2026 10:00:00 +0500",
            is_unread=False, labels=["INBOX"],
        ),
        EmailMessage(
            id="mock004", thread_id="t004",
            subject="Interview feedback needed — Candidate: Farhan K.",
            sender="HR Team", sender_email="hr@company.com",
            snippet="Please submit your interview feedback for Farhan K. by today 3pm.",
            body="Hi,\n\nWe need your interview feedback for Farhan K. by 3:00 PM today so we can make a hiring decision.\n\nPlease fill out the form: [link]\n\nThanks,\nHR Team",
            date="Thu, 16 Apr 2026 09:45:00 +0500",
            is_unread=True, labels=["INBOX", "UNREAD", "IMPORTANT"],
        ),
        EmailMessage(
            id="mock005", thread_id="t005",
            subject="Weekly newsletter: AI tools roundup",
            sender="TechBrief", sender_email="newsletter@techbrief.io",
            snippet="This week in AI: Claude 4, GPT-5, and the new wave of coding agents.",
            body="Weekly roundup of AI tools and news...",
            date="Thu, 16 Apr 2026 07:00:00 +0500",
            is_unread=True, labels=["INBOX", "UNREAD"],
        ),
    ]
