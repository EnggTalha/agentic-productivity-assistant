"""
main.py — CLI entry point for the Personal AI Chief of Staff.

Usage:
  python main.py                        # run morning brief now
  python main.py --dry-run              # simulate without sending anything
  python main.py --schedule             # run daily at BRIEF_HOUR (daemon mode)
  python main.py --emails-only          # just triage emails
  python main.py --brief-only           # just generate brief (no email actions)
"""

import argparse
import sys
from rich.console import Console
from config import EnvConfig

console = Console()


def validate_env() -> bool:
    errors = []
    if not EnvConfig.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set")
    if not EnvConfig.YOUR_NAME:
        errors.append("YOUR_NAME is not set")
    if not EnvConfig.YOUR_EMAIL:
        errors.append("YOUR_EMAIL is not set")
    if errors:
        console.print("[bold red]Configuration errors:[/bold red]")
        for e in errors:
            console.print(f"  [red]✗[/red] {e}")
        console.print("\nCopy [dim].env.example[/dim] → [dim].env[/dim] and fill in your values.")
        console.print("See [dim]SETUP.md[/dim] for Google OAuth setup (~5 min).")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Personal AI Chief of Staff — powered by Claude"
    )
    parser.add_argument("--dry-run",     action="store_true", help="Simulate — no emails sent, no Slack messages")
    parser.add_argument("--live",        action="store_true", help="Live mode — actually send drafts and Slack messages")
    parser.add_argument("--schedule",    action="store_true", help="Run as daily daemon at BRIEF_HOUR")
    parser.add_argument("--emails-only", action="store_true", help="Only triage emails, skip brief")
    parser.add_argument("--brief-only",  action="store_true", help="Generate brief without applying email actions")
    args = parser.parse_args()

    if args.dry_run:
        EnvConfig.DRY_RUN = True
    if args.live:
        EnvConfig.DRY_RUN = False

    if not validate_env():
        sys.exit(1)

    if args.schedule:
        _run_scheduled()
    else:
        from agent.orchestrator import ChiefOfStaffAgent
        ChiefOfStaffAgent().run()


def _run_scheduled():
    """Run as a daily daemon — fires at BRIEF_HOUR every day."""
    import time
    from datetime import datetime
    import pytz

    brief_hour = int(EnvConfig.TIMEZONE)  # uses BRIEF_HOUR env
    tz = pytz.timezone(EnvConfig.TIMEZONE)

    console.print(f"[cyan]Scheduled mode:[/cyan] Running daily at {EnvConfig.TIMEZONE}")
    console.print("Press Ctrl+C to stop.\n")

    while True:
        now = datetime.now(tz)
        if now.hour == int(open('.env').read().split('BRIEF_HOUR=')[1].split('\n')[0] if 'BRIEF_HOUR=' in open('.env').read() else "8"):
            from agent.orchestrator import ChiefOfStaffAgent
            ChiefOfStaffAgent().run()
            time.sleep(60 * 60)  # wait 1 hour before checking again
        else:
            time.sleep(60)  # check every minute


if __name__ == "__main__":
    main()
