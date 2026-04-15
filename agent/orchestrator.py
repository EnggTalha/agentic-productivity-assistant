"""
agent/orchestrator.py — Main agentic loop for the Personal AI Chief of Staff.

Flow:
1. Fetch emails (Gmail API — free)
2. Fetch today's calendar (Google Calendar API — free)
3. Claude triages emails → actions + draft replies
4. Claude extracts tasks from emails + meetings
5. Claude generates personalized morning brief
6. Apply email actions (drafts, archives)
7. Deliver brief to Slack + save Markdown
"""

from __future__ import annotations
from rich.console import Console
from rich.panel import Panel

from config import EnvConfig
from tools.gmail_tool import fetch_recent_emails, send_draft, archive_email, mark_read
from tools.calendar_tool import fetch_todays_events
from tools.slack_tool import deliver_brief_to_slack
from tools.reporter import print_brief, save_brief_markdown, save_brief_json
from agent.brain import triage_emails, extract_tasks, generate_daily_brief

console = Console()


class ChiefOfStaffAgent:
    """Personal AI Chief of Staff — runs every morning."""

    def run(self) -> None:
        console.print(Panel.fit(
            f"[bold cyan]Personal AI Chief of Staff[/bold cyan]\n"
            f"Agent for: [bold]{EnvConfig.YOUR_NAME}[/bold] ({EnvConfig.YOUR_ROLE})\n"
            f"Mode: {'[yellow]DRY RUN[/yellow]' if EnvConfig.DRY_RUN else '[green]LIVE[/green]'} | "
            f"TZ: {EnvConfig.TIMEZONE}",
            border_style="cyan",
        ))

        # ── Step 1: Fetch emails ────────────────────────────────────────
        console.print("\n[bold cyan]📬 Fetching emails...[/bold cyan]")
        emails = fetch_recent_emails(max_results=EnvConfig.MAX_EMAILS)

        # ── Step 2: Fetch calendar ──────────────────────────────────────
        console.print("\n[bold cyan]📅 Fetching calendar...[/bold cyan]")
        events = fetch_todays_events()

        # ── Step 3: Triage emails ───────────────────────────────────────
        console.print("\n[bold cyan]🧠 Triaging emails...[/bold cyan]")
        actions = triage_emails(emails)

        # ── Step 4: Extract tasks ───────────────────────────────────────
        console.print("\n[bold cyan]✅ Extracting tasks...[/bold cyan]")
        tasks = extract_tasks(emails, events)

        # ── Step 5: Generate brief ──────────────────────────────────────
        console.print("\n[bold cyan]📋 Generating morning brief...[/bold cyan]")
        brief = generate_daily_brief(emails, events, actions, tasks)

        # ── Step 6: Apply email actions ─────────────────────────────────
        console.print("\n[bold cyan]⚙️  Applying email actions...[/bold cyan]")
        drafted = 0
        archived = 0
        for action in actions:
            if action.action == "reply" and action.draft_reply and drafted < EnvConfig.MAX_DRAFTS:
                email = next((e for e in emails if e.id == action.email_id), None)
                if email:
                    ok = send_draft(
                        email_id=email.thread_id,
                        reply_body=action.draft_reply,
                        to=email.sender_email,
                        subject=email.subject,
                    )
                    if ok:
                        drafted += 1

            elif action.action == "archive":
                if archive_email(action.email_id):
                    archived += 1

        console.print(f"  [green]✓[/green] {drafted} drafts created, {archived} emails archived.")

        # ── Step 7: Deliver + save ──────────────────────────────────────
        print_brief(brief)

        md_path   = save_brief_markdown(brief)
        json_path = save_brief_json(brief)
        slack_ok  = deliver_brief_to_slack(brief)

        console.print(f"\n[bold green]✓ Chief of Staff run complete![/bold green]")
        console.print(f"  📄 Brief saved: [dim]{md_path}[/dim]")
        if slack_ok:
            console.print(f"  💬 Delivered to Slack.")
        console.print()
