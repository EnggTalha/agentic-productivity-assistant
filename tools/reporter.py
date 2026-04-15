"""
tools/reporter.py — Print beautiful terminal brief and save Markdown report.
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich import box

from config import DailyBrief, BRIEFS_DIR

console = Console()

PRIORITY_COLOR = {"urgent": "red", "high": "orange3", "normal": "yellow", "low": "green"}
PRIORITY_EMOJI = {"urgent": "🔴", "high": "🟠", "normal": "🟡", "low": "🟢"}
ACTION_EMOJI   = {"reply": "✉️", "flag": "🚩", "archive": "📦", "ignore": "🗑️"}


def print_brief(brief: DailyBrief) -> None:
    """Print the morning brief beautifully in the terminal."""
    console.print()
    console.print(Panel(
        f"[bold cyan]{brief.greeting}[/bold cyan]",
        border_style="cyan", padding=(1, 2),
    ))

    # Executive summary
    console.print(Panel(
        brief.executive_summary,
        title="[bold]📋 Today's Overview[/bold]",
        border_style="dim", padding=(0, 1),
    ))

    # Schedule
    if brief.todays_schedule:
        sched_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        sched_table.add_column("Time", width=12)
        sched_table.add_column("Meeting")
        sched_table.add_column("With", max_width=30)
        for e in brief.todays_schedule:
            time_str = _fmt_time(e.start)
            attendees = ", ".join(e.attendees[:2]) + ("..." if len(e.attendees) > 2 else "")
            sched_table.add_row(time_str, e.title, attendees or "—")
        console.print(Panel(sched_table, title="[bold]📅 Schedule[/bold]", border_style="blue"))

    # Tasks
    if brief.priority_tasks:
        task_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        task_table.add_column("P", width=3)
        task_table.add_column("Task")
        task_table.add_column("Due", width=14)
        task_table.add_column("Source", width=10)
        for t in brief.priority_tasks[:8]:
            color = PRIORITY_COLOR.get(t.priority, "white")
            task_table.add_row(
                f"[{color}]{PRIORITY_EMOJI.get(t.priority, '⚪')}[/{color}]",
                t.title,
                t.due or "today",
                t.source,
            )
        console.print(Panel(task_table, title="[bold]✅ Priority Tasks[/bold]", border_style="green"))

    # Email actions
    if brief.email_actions:
        email_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        email_table.add_column("Action", width=10)
        email_table.add_column("From", max_width=20)
        email_table.add_column("Subject", max_width=40)
        email_table.add_column("P", width=3)
        for a in brief.email_actions:
            color = PRIORITY_COLOR.get(a.priority, "white")
            email_table.add_row(
                f"{ACTION_EMOJI.get(a.action, '?')} {a.action}",
                a.sender[:20],
                a.subject[:40],
                f"[{color}]{a.priority[0].upper()}[/{color}]",
            )
        console.print(Panel(email_table, title="[bold]📬 Email Actions[/bold]", border_style="yellow"))

    # Bottom row: focus + watch out + quick wins
    focus_text  = f"[bold]⏰ Focus Block[/bold]\n{brief.focus_block}"
    watch_text  = "[bold]👀 Watch Out[/bold]\n" + "\n".join(f"• {w}" for w in brief.watch_out)
    wins_text   = "[bold]⚡ Quick Wins[/bold]\n" + "\n".join(f"• {w}" for w in brief.quick_wins)

    console.print(Panel(
        f"{focus_text}\n\n{watch_text}\n\n{wins_text}",
        border_style="magenta", padding=(0, 1),
    ))

    console.print(Panel(
        f"[italic]{brief.motivational_note}[/italic]",
        border_style="dim", padding=(0, 2),
    ))
    console.print()


def save_brief_markdown(brief: DailyBrief) -> Path:
    """Save the brief as a Markdown file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = BRIEFS_DIR / f"brief_{ts}.md"

    lines = [
        f"# 🌅 Morning Brief — {brief.date}",
        f"",
        f"> {brief.greeting}",
        f"",
        f"## 📋 Overview",
        brief.executive_summary,
        f"",
        f"---",
        f"",
        f"## 📅 Today's Schedule",
        f"",
        f"| Time | Meeting | Attendees |",
        f"|---|---|---|",
    ]
    for e in brief.todays_schedule:
        attendees = ", ".join(e.attendees[:3])
        lines.append(f"| {_fmt_time(e.start)} | {e.title} | {attendees or '—'} |")

    lines += ["", "## ✅ Priority Tasks", ""]
    for t in brief.priority_tasks:
        emoji = PRIORITY_EMOJI.get(t.priority, "⚪")
        due = f" _(due: {t.due})_" if t.due else ""
        lines.append(f"- {emoji} **{t.title}**{due} — _{t.context}_")

    lines += ["", "## 📬 Email Actions", ""]
    for a in brief.email_actions:
        emoji = ACTION_EMOJI.get(a.action, "?")
        lines.append(f"- {emoji} **{a.action.upper()}** — {a.subject} from {a.sender}")
        lines.append(f"  > {a.reason}")
        if a.draft_reply:
            lines += ["", f"  **Draft reply:**", f"  ```", a.draft_reply, f"  ```", ""]

    lines += [
        "",
        f"## ⏰ Focus Block",
        brief.focus_block,
        "",
        f"## 👀 Watch Out For",
    ]
    for w in brief.watch_out:
        lines.append(f"- ⚠️ {w}")

    lines += ["", "## ⚡ Quick Wins"]
    for q in brief.quick_wins:
        lines.append(f"- {q}")

    lines += ["", "---", f"_{brief.motivational_note}_"]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]✓[/green] Brief saved → {out_path}")
    return out_path


def save_brief_json(brief: DailyBrief) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = BRIEFS_DIR / f"brief_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(brief.model_dump(), f, indent=2, default=str)
    return out_path


def _fmt_time(dt_str: str) -> str:
    try:
        from dateutil import parser
        return parser.parse(dt_str).strftime("%I:%M %p")
    except Exception:
        return dt_str[11:16] if len(dt_str) > 15 else dt_str
