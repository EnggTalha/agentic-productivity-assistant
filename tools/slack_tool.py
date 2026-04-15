"""
tools/slack_tool.py — Deliver the morning brief via Slack.
Uses Slack Bolt (free — just needs a bot token).
Falls back to terminal print if not configured.
"""

from __future__ import annotations
from rich.console import Console
from config import EnvConfig, DailyBrief

console = Console()


def deliver_brief_to_slack(brief: DailyBrief) -> bool:
    """Post the morning brief to Slack channel."""
    if not EnvConfig.SLACK_BOT_TOKEN or not EnvConfig.SLACK_CHANNEL_ID:
        console.print("[dim]Slack not configured — brief printed to terminal only.[/dim]")
        return False

    if EnvConfig.DRY_RUN:
        console.print("[yellow][DRY RUN][/yellow] Would post brief to Slack.")
        return True

    try:
        import requests

        blocks = _build_slack_blocks(brief)
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {EnvConfig.SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "channel": EnvConfig.SLACK_CHANNEL_ID,
                "text": f"🌅 Morning Brief — {brief.date}",
                "blocks": blocks,
            },
            timeout=10,
        )

        data = response.json()
        if data.get("ok"):
            console.print(f"[green]✓[/green] Morning brief delivered to Slack.")
            return True
        else:
            console.print(f"[red]Slack error:[/red] {data.get('error', 'unknown')}")
            return False

    except Exception as e:
        console.print(f"[red]Slack delivery failed:[/red] {e}")
        return False


def _build_slack_blocks(brief: DailyBrief) -> list:
    """Build rich Slack block kit message."""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🌅 Morning Brief — {brief.date}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_{brief.greeting}_"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📋 Summary*\n{brief.executive_summary}"},
        },
    ]

    # Today's schedule
    if brief.todays_schedule:
        schedule_lines = "\n".join([
            f"• *{_fmt_time(e.start)}* — {e.title}" + (f" _{len(e.attendees)} attendees_" if e.attendees else "")
            for e in brief.todays_schedule
        ])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*📅 Today's Schedule*\n{schedule_lines}"},
        })

    # Priority tasks
    if brief.priority_tasks:
        priority_map = {"urgent": "🔴", "high": "🟠", "normal": "🟡", "low": "🟢"}
        task_lines = "\n".join([
            f"{priority_map.get(t.priority, '⚪')} {t.title}"
            for t in brief.priority_tasks[:5]
        ])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*✅ Priority Tasks*\n{task_lines}"},
        })

    # Watch out
    if brief.watch_out:
        watch_lines = "\n".join([f"⚠️ {w}" for w in brief.watch_out])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*👀 Watch Out For*\n{watch_lines}"},
        })

    # Focus block + motivational note
    blocks.append({
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*⏰ Focus Block*\n{brief.focus_block}"},
            {"type": "mrkdwn", "text": f"*💡 Today's Note*\n_{brief.motivational_note}_"},
        ],
    })

    return blocks


def _fmt_time(dt_str: str) -> str:
    """Format ISO datetime to HH:MM."""
    try:
        from dateutil import parser
        dt = parser.parse(dt_str)
        return dt.strftime("%I:%M %p")
    except Exception:
        return dt_str[:16]
