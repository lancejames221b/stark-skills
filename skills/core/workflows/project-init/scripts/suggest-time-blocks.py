#!/usr/bin/env python3
"""
suggest-time-blocks.py — Fetch calendar and suggest focus time blocks for a project.

Usage:
  python3 suggest-time-blocks.py --ticket-count N --complexity medium [--weeks 2]

Arguments:
  --ticket-count   Number of tickets in the project
  --complexity     Estimated complexity: low | medium | high
  --weeks          How many weeks ahead to look (default: 2)

Outputs suggested time blocks as formatted markdown, with ISO timestamps
suitable for calendar event creation.

Hour estimates per complexity:
  low    = 1h per ticket
  medium = 2h per ticket
  high   = 4h per ticket

Work hours: 9:00 AM – 6:00 PM EST, Monday–Friday only.
Block minimum: 2 hours.
Suggests 3–5 blocks totaling ~= estimated hours.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
import zoneinfo

CALENDAR_EMAIL = os.environ.get("CALENDAR_EMAIL", "you@yourdomain.com")
WORK_TZ = zoneinfo.ZoneInfo("America/New_York")
WORK_START_HOUR = 9   # 9 AM
WORK_END_HOUR = 18    # 6 PM
MIN_BLOCK_HOURS = 2
MAX_SUGGESTIONS = 5
MIN_SUGGESTIONS = 3

COMPLEXITY_HOURS = {
    "low": 1,
    "medium": 2,
    "high": 4,
}


def fetch_calendar_events(start_iso: str, end_iso: str) -> list[dict]:
    """
    Fetch calendar events via mcporter google-workspace.
    Returns list of event dicts with 'start' and 'end' keys (ISO strings).
    """
    cmd = [
        "mcporter", "call", "google-workspace.search_calendar",
        f"user_google_email={CALENDAR_EMAIL}",
        f"start_time={start_iso}",
        f"end_time={end_iso}",
        "max_results=100",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"WARNING: Calendar fetch failed (exit {result.returncode}). Proceeding without events.", file=sys.stderr)
        if result.stderr:
            print(f"  STDERR: {result.stderr[:300]}", file=sys.stderr)
        return []

    raw = result.stdout.strip()
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"WARNING: Could not parse calendar response as JSON. Raw: {raw[:200]}", file=sys.stderr)
        return []

    # Handle mcporter-wrapped response
    events = data
    for key in ("result", "data", "events", "items"):
        if key in data and isinstance(data[key], list):
            events = data[key]
            break

    if not isinstance(events, list):
        return []

    parsed = []
    for ev in events:
        start = ev.get("start") or {}
        end = ev.get("end") or {}
        start_str = start.get("dateTime") or start.get("date") or (start if isinstance(start, str) else "")
        end_str = end.get("dateTime") or end.get("date") or (end if isinstance(end, str) else "")
        if start_str and end_str:
            parsed.append({"start": start_str, "end": end_str, "summary": ev.get("summary", "")})

    return parsed


def parse_iso(s: str) -> datetime | None:
    """Parse ISO 8601 string to timezone-aware datetime (EST)."""
    if not s:
        return None
    # Handle date-only strings (all-day events)
    if "T" not in s and len(s) == 10:
        try:
            d = datetime.strptime(s, "%Y-%m-%d")
            return d.replace(hour=0, minute=0, second=0, tzinfo=WORK_TZ)
        except ValueError:
            return None
    # Try common ISO formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M%z"):
        try:
            dt = datetime.strptime(s.replace("Z", "+00:00"), fmt)
            return dt.astimezone(WORK_TZ)
        except ValueError:
            continue
    try:
        # Python 3.11+ fromisoformat handles most cases
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=WORK_TZ)
        return dt.astimezone(WORK_TZ)
    except ValueError:
        return None


def is_business_day(dt: datetime) -> bool:
    """Return True if dt is Monday–Friday."""
    return dt.weekday() < 5  # 0=Mon, 4=Fri


def find_free_blocks(
    events: list[dict],
    search_start: datetime,
    search_end: datetime,
    block_hours: int = MIN_BLOCK_HOURS,
) -> list[tuple[datetime, datetime]]:
    """
    Find free time blocks of >= block_hours hours during work hours on weekdays.
    Returns list of (start, end) datetime tuples (timezone-aware, EST).
    """
    # Build busy intervals from events
    busy: list[tuple[datetime, datetime]] = []
    for ev in events:
        ev_start = parse_iso(ev["start"])
        ev_end = parse_iso(ev["end"])
        if ev_start and ev_end:
            busy.append((ev_start, ev_end))
    busy.sort(key=lambda x: x[0])

    free_blocks: list[tuple[datetime, datetime]] = []
    current_day = search_start.replace(hour=0, minute=0, second=0, microsecond=0)

    while current_day < search_end:
        if not is_business_day(current_day):
            current_day += timedelta(days=1)
            continue

        day_work_start = current_day.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
        day_work_end = current_day.replace(hour=WORK_END_HOUR, minute=0, second=0, microsecond=0)

        # Skip days in the past
        now = datetime.now(tz=WORK_TZ)
        if day_work_end < now:
            current_day += timedelta(days=1)
            continue
        if day_work_start < now:
            day_work_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        # Find free slots in this day
        slot_start = day_work_start
        day_busy = [
            (s, e) for (s, e) in busy
            if s < day_work_end and e > day_work_start
        ]
        day_busy.sort(key=lambda x: x[0])

        for b_start, b_end in day_busy:
            b_start = max(b_start, day_work_start)
            b_end = min(b_end, day_work_end)
            if slot_start < b_start:
                gap_hours = (b_start - slot_start).total_seconds() / 3600
                if gap_hours >= block_hours:
                    # Clip to requested block_hours
                    block_end = slot_start + timedelta(hours=block_hours)
                    free_blocks.append((slot_start, block_end))
            slot_start = max(slot_start, b_end)

        # Check remaining time after last busy slot
        if slot_start < day_work_end:
            gap_hours = (day_work_end - slot_start).total_seconds() / 3600
            if gap_hours >= block_hours:
                block_end = slot_start + timedelta(hours=block_hours)
                free_blocks.append((slot_start, block_end))

        current_day += timedelta(days=1)

    return free_blocks


def format_block(start: datetime, end: datetime, index: int) -> str:
    """Format a time block as a markdown list item."""
    day_name = start.strftime("%A")
    date_str = start.strftime("%b %d")
    start_time = start.strftime("%I:%M %p").lstrip("0")
    end_time = end.strftime("%I:%M %p").lstrip("0")
    hours = int((end - start).total_seconds() / 3600)
    iso_start = start.isoformat()
    iso_end = end.isoformat()

    return (
        f"{index}. **{day_name} {date_str}** — {start_time}–{end_time} EST "
        f"({hours}h)\n"
        f"   `START={iso_start}` `END={iso_end}`"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Suggest focus time blocks for a project based on calendar availability."
    )
    parser.add_argument(
        "--ticket-count",
        type=int,
        required=True,
        help="Number of tickets/tasks in the project.",
    )
    parser.add_argument(
        "--complexity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Estimated ticket complexity: low (1h), medium (2h), high (4h). Default: medium.",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=2,
        help="How many weeks ahead to search for slots. Default: 2.",
    )
    parser.add_argument(
        "--block-hours",
        type=int,
        default=MIN_BLOCK_HOURS,
        help=f"Minimum block size in hours. Default: {MIN_BLOCK_HOURS}.",
    )
    args = parser.parse_args()

    if args.ticket_count < 1:
        print("ERROR: --ticket-count must be >= 1.", file=sys.stderr)
        sys.exit(1)

    hours_per_ticket = COMPLEXITY_HOURS[args.complexity]
    total_hours = args.ticket_count * hours_per_ticket

    now = datetime.now(tz=WORK_TZ)
    search_start = now
    search_end = now + timedelta(weeks=args.weeks)

    search_start_iso = search_start.isoformat()
    search_end_iso = search_end.isoformat()

    # Fetch calendar events
    events = fetch_calendar_events(search_start_iso, search_end_iso)

    # Find free blocks
    free_blocks = find_free_blocks(
        events,
        search_start,
        search_end,
        block_hours=args.block_hours,
    )

    if not free_blocks:
        print(f"## ⚠️ No free {args.block_hours}h+ blocks found in the next {args.weeks} weeks")
        print(f"\nEstimated work: **~{total_hours} hours** ({args.ticket_count} tickets × {hours_per_ticket}h/{args.complexity} complexity)")
        print("\nConsider checking your calendar manually or extending the search window with `--weeks 3`.")
        sys.exit(0)

    # Select up to MAX_SUGGESTIONS blocks totaling roughly total_hours
    selected: list[tuple[datetime, datetime]] = []
    accumulated = 0
    for block_start, block_end in free_blocks:
        if len(selected) >= MAX_SUGGESTIONS:
            break
        selected.append((block_start, block_end))
        accumulated += (block_end - block_start).total_seconds() / 3600
        if accumulated >= total_hours and len(selected) >= MIN_SUGGESTIONS:
            break

    # Output markdown
    print(f"## 📅 Suggested Focus Blocks\n")
    print(f"**Estimated work:** ~{total_hours} hours ({args.ticket_count} tickets × {hours_per_ticket}h each, {args.complexity} complexity)")
    print(f"**Scheduled:** {accumulated:.0f}h across {len(selected)} blocks")
    print()

    for i, (bstart, bend) in enumerate(selected, 1):
        print(format_block(bstart, bend, i))
        print()

    print("---")
    print("*Copy a `START=` / `END=` value above to create a calendar event.*")
    print(f"*Calendar: `{CALENDAR_EMAIL}` · Timezone: America/New_York*")


if __name__ == "__main__":
    main()
