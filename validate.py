#!/usr/bin/env python3
"""Validates global_events.json against RaceBound Garage's actual base-game
content pools, so a typo'd or unavailable car/track fails CI instead of
silently falling back at runtime with no feedback.

This is a SNAPSHOT of scripts/core/licenses.gd's LOANER_POOL / LOANER_SKIP /
BASE_TRACKS from the main game repo (private, so this public repo can't read
it directly) and GlobalEvent.MAX_LAP_M. If the game's pools ever change,
re-sync this list by hand — they're pinned to Kunos base-game content and
rarely change.

Usage: python validate.py [path-to-json, defaults to global_events.json]
Exit code 0 = all entries valid. Exit code 1 = at least one problem found
(printed to stderr, one line per problem).
"""
import json
import sys

# Mirrors scripts/core/global_event.gd's SECONDS_PER_WEEK / WEEK_OFFSET_SEC.
# Raw Unix-epoch week boundaries land on Thursday 00:00 UTC (Jan 1 1970 was
# a Thursday) — this shifts them 3 days earlier to land on Monday 00:00 UTC,
# the actual intended weekly reset day. If the game's offset ever changes,
# update it here too — these MUST stay in sync or generated week_index
# values won't line up with what the game itself considers "this week."
SECONDS_PER_WEEK = 604800
WEEK_OFFSET_SEC = 3 * 86400


def week_index_for_timestamp(ts: float) -> int:
    return int((ts + WEEK_OFFSET_SEC) // SECONDS_PER_WEEK)


VALID_CARS = {
    "abarth500", "abarth500_s1", "alfa_romeo_giulietta_qv", "alfa_romeo_giulietta_qv_le",
    "bmw_1m", "bmw_1m_s3", "bmw_m3_e30", "bmw_m3_e30_dtm", "bmw_m3_e30_gra", "bmw_m3_e30_s1",
    "bmw_m3_e92", "bmw_m3_e92_s1", "bmw_m3_gt2", "bmw_z4", "bmw_z4_gt3", "bmw_z4_s1",
    "ferrari_312t", "ferrari_458", "ferrari_458_gt2", "ferrari_458_s3", "ferrari_599xxevo",
    "ferrari_f40", "ferrari_f40_s3", "ferrari_laferrari",
    "ktm_xbow_r", "lotus_2_eleven", "lotus_2_eleven_gt4", "lotus_49", "lotus_98t",
    "lotus_elise_sc", "lotus_elise_sc_s1", "lotus_elise_sc_s2", "lotus_evora_gtc",
    "lotus_evora_gte", "lotus_evora_gte_carbon", "lotus_evora_gx", "lotus_evora_s",
    "lotus_evora_s_s2", "lotus_exige_240", "lotus_exige_240_s3", "lotus_exige_s",
    "lotus_exige_s_roadster", "lotus_exige_scura", "lotus_exos_125", "lotus_exos_125_s1",
    "mclaren_mp412c", "mclaren_mp412c_gt3", "mercedes_sls", "mercedes_sls_gt3",
    "p4-5_2010", "pagani_huayra", "pagani_zonda_r", "ruf_yellowbird",
    "shelby_cobra_427sc", "tatuusfa1",
}
# Drift-spec loaners the game itself excludes from selection — never valid here either.
LOANER_SKIP = {"bmw_m3_e30_drift", "bmw_m3_e92_drift", "bmw_z4_drift"}

VALID_TRACKS = {
    "magione", "imola", "monza", "mugello", "spa",
    "ks_silverstone", "ks_silverstone1967", "ks_vallelunga",
    "ks_nurburgring", "ks_zandvoort", "ks_laguna_seca",
    "ks_black_cat_county", "ks_highlands", "ks_monza66",
}


def validate(data: dict) -> list[str]:
    errors = []
    if not isinstance(data, dict) or "events" not in data:
        return ['Top level must be an object with an "events" key.']
    events = data["events"]
    if not isinstance(events, dict):
        return ['"events" must be an object keyed by week_index.']

    for week_key, entry in events.items():
        prefix = f'week "{week_key}"'
        if not week_key.isdigit():
            errors.append(f"{prefix}: key must be a plain integer string (a week_index), not {week_key!r}")
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: entry must be an object, got {type(entry).__name__}")
            continue

        car = entry.get("car", "")
        track = entry.get("track", "")
        layout = entry.get("layout", "")

        if not isinstance(car, str) or car not in VALID_CARS:
            errors.append(f'{prefix}: car "{car}" is not in the base-game loaner pool')
        elif car in LOANER_SKIP:
            errors.append(f'{prefix}: car "{car}" is a drift-spec loaner, excluded from selection')

        if not isinstance(track, str) or track not in VALID_TRACKS:
            errors.append(f'{prefix}: track "{track}" is not in the base-game track pool')

        if not isinstance(layout, str):
            errors.append(f'{prefix}: "layout" must be a string (use "" for a track\'s default layout)')

        # Note: this script has no way to check the LAYOUT itself is real, or
        # that the resulting track length stays under GlobalEvent.MAX_LAP_M
        # (8000m) — that data only exists in each player's own scanned AC
        # install, not here. ks_highlands specifically has both a short
        # circuit layout and a ~12km "Long" point-to-point layout that
        # exceeds the cap (see the game's own commit history for why) — the
        # runtime's own validation in GlobalEvent._override_for_cycle()
        # still catches this if you get a layout wrong, same as always.

    return errors


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "global_events.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Could not read/parse {path}: {e}", file=sys.stderr)
        return 1

    errors = validate(data)
    if errors:
        print(f"{path} FAILED validation:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    n = len(data.get("events", {}))
    print(f"{path} OK — {n} week entr{'y' if n == 1 else 'ies'} valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
