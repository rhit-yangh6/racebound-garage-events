#!/usr/bin/env python3
"""Adds (or overwrites) one week's entry in global_events.json — validates
the car/track locally before ever touching the file, and computes
week_index for you so you never have to do the date math by hand.

Examples:
    # Explicit date - the entry applies to whichever week that date falls in.
    python add_week.py --car ferrari_458 --track monza --date 2026-08-06

    # No --date/--week given: uses the next week_index not already in the file.
    python add_week.py --car mercedes_sls --track spa --note "Spa week"

    # Explicit week_index, if you already know it (e.g. from the printed table).
    python add_week.py --car bmw_z4_gt3 --track ks_nurburgring --week 2960

This only edits global_events.json on disk — it does NOT commit or push.
Review the diff (`git diff`) and push yourself once it looks right; `validate.py`
will also re-run automatically in CI the moment you push.
"""
import argparse
import datetime
import json
import sys

from validate import VALID_CARS, LOANER_SKIP, VALID_TRACKS, SECONDS_PER_WEEK, WEEK_OFFSET_SEC, week_index_for_timestamp


def week_index_for_date(date_str: str) -> int:
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    return week_index_for_timestamp(d.timestamp())


def next_free_week(events: dict) -> int:
    now_week = week_index_for_timestamp(datetime.datetime.now(datetime.timezone.utc).timestamp())
    existing = {int(k) for k in events if k.isdigit()}
    w = max(existing, default=now_week - 1) + 1
    if not existing:
        w = max(w, now_week)
    return w


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--car", required=True, help="car folder, e.g. ferrari_458")
    ap.add_argument("--track", required=True, help="track folder, e.g. monza")
    ap.add_argument("--layout", default="", help='layout name, or "" (default) for the track\'s only/default layout')
    ap.add_argument("--note", default="", help="optional human-readable label, ignored by the game")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--week", type=int, help="explicit week_index")
    group.add_argument("--date", help="a date (YYYY-MM-DD) inside the target week")
    ap.add_argument("--file", default="global_events.json", help="path to the events JSON (default: global_events.json)")
    args = ap.parse_args()

    if args.car not in VALID_CARS:
        print(f'Refusing: "{args.car}" is not in the base-game loaner pool.', file=sys.stderr)
        return 1
    if args.car in LOANER_SKIP:
        print(f'Refusing: "{args.car}" is a drift-spec loaner, excluded from selection.', file=sys.stderr)
        return 1
    if args.track not in VALID_TRACKS:
        print(f'Refusing: "{args.track}" is not in the base-game track pool.', file=sys.stderr)
        return 1

    try:
        with open(args.file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"events": {}}
    events = data.setdefault("events", {})

    if args.week is not None:
        week = args.week
    elif args.date:
        week = week_index_for_date(args.date)
    else:
        week = next_free_week(events)

    entry = {"car": args.car, "track": args.track, "layout": args.layout}
    if args.note:
        entry["note"] = args.note

    overwriting = str(week) in events
    events[str(week)] = entry

    with open(args.file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    action = "Overwrote" if overwriting else "Added"
    start = datetime.datetime.fromtimestamp(week * SECONDS_PER_WEEK - WEEK_OFFSET_SEC, tz=datetime.timezone.utc)
    print(f"{action} week {week} (starts {start:%Y-%m-%d}): {args.car} @ {args.track}"
          + (f" [{args.layout}]" if args.layout else ""))
    print(f"Wrote {args.file} — review with `git diff`, then commit and push when ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
