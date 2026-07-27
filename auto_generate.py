#!/usr/bin/env python3
"""Auto-generates upcoming Global Event weeks, avoiding recent repeats.

Reads global_events.json's own history to know what's been used recently,
fills in any week in a rolling window ahead of the current week that isn't
already covered (WINDOW_WEEKS, default 4 = this week + the next 3), and
writes the result back. Run on a schedule via
.github/workflows/auto_generate.yml; safe to re-run any time — a no-op if
the window is already fully populated, and it NEVER overwrites an
already-existing entry (manually curated or previously auto-generated).

Selection avoids repeating a car within CAR_COOLDOWN weeks, or a track
within TRACK_COOLDOWN weeks, of its most recent use — falling back to the
full pool if the exclusion would leave nothing to pick from, so it can
never get stuck even as the history grows.
"""
import datetime
import json
import random
import sys

from validate import VALID_CARS, LOANER_SKIP, VALID_TRACKS, validate, week_index_for_timestamp

WINDOW_WEEKS = 4     # always keep this many weeks (including the current one) filled
CAR_COOLDOWN = 20    # weeks before a car can repeat
TRACK_COOLDOWN = 6   # weeks before a track can repeat (only 14 tracks total)

ELIGIBLE_CARS = sorted(VALID_CARS - LOANER_SKIP)
ELIGIBLE_TRACKS = sorted(VALID_TRACKS)


def current_week_index() -> int:
    return week_index_for_timestamp(datetime.datetime.now(datetime.timezone.utc).timestamp())


def recent_picks(events: dict, target_week: int, cooldown: int, field: str) -> set:
    """Values used for `field` in any week within `cooldown` weeks before target_week."""
    recent = set()
    for week_key, entry in events.items():
        if not week_key.isdigit() or not isinstance(entry, dict):
            continue
        w = int(week_key)
        if target_week - cooldown <= w < target_week:
            recent.add(entry.get(field, ""))
    return recent


def pick_for_week(events: dict, week: int, rng: random.Random) -> dict:
    recent_cars = recent_picks(events, week, CAR_COOLDOWN, "car")
    recent_tracks = recent_picks(events, week, TRACK_COOLDOWN, "track")

    car_choices = [c for c in ELIGIBLE_CARS if c not in recent_cars] or ELIGIBLE_CARS
    track_choices = [t for t in ELIGIBLE_TRACKS if t not in recent_tracks] or ELIGIBLE_TRACKS

    return {
        "car": rng.choice(car_choices),
        "track": rng.choice(track_choices),
        "layout": "",
        "note": "auto-generated",
    }


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "global_events.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"events": {}}
    events = data.setdefault("events", {})

    rng = random.Random()  # unseeded — a real, unpredictable pick each run
    now = current_week_index()
    added = []
    for week in range(now, now + WINDOW_WEEKS):
        if str(week) in events:
            continue
        entry = pick_for_week(events, week, rng)
        events[str(week)] = entry
        added.append((week, entry))

    if not added:
        print("Nothing to do — the rolling window is already fully populated.")
        return 0

    errors = validate(data)
    if errors:
        # Should never happen (only ever picks from the validated pools),
        # but never write/commit anything that hasn't been safety-checked.
        print("Generated entries failed validation — aborting, nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    for week, entry in added:
        print(f"Generated week {week}: {entry['car']} @ {entry['track']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
