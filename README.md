# racebound-garage-events

Weekly Global Event picks for RaceBound Garage, fetched at runtime from
`global_events.json`. A week with no entry here just falls back to the
game's own deterministic pick — nothing needs to be filled in ahead of time.

## Auto-generation (default — no manual work needed)

`.github/workflows/auto_generate.yml` runs every Wednesday at 21:00 UTC —
3 hours before the actual weekly reset (Monday 00:00 UTC, see below) —
and can also be triggered manually via "Run workflow". It keeps the next
4 weeks always filled, avoiding a repeat car within 20 weeks or a repeat
track within 6 weeks of its last use, falling back to the full pool if
that ever leaves nothing to pick from. It only ever fills weeks that
don't already have an entry, so hand-curated weeks (see below) are never
touched or overwritten. It commits straight to `main` — this is meant to
run with zero ongoing attention.

## Hand-picking a specific week (optional)

If you want to override a specific week instead of leaving it to
auto-generation:

```
python add_week.py --car ferrari_458 --track monza --date 2026-08-06
```

Validates the car/track locally before writing anything, and computes
`week_index` for you (or just omit `--date`/`--week` to use the next week
not already covered). Review with `git diff`, then commit and push.

## Validation

`validate.py` checks every entry against the game's actual base-game
content pools. It runs automatically in CI on every push via
`.github/workflows/validate.yml` — a bad car/track name fails the check
instead of silently reaching players. For it to actually *gate* a bad push
before it goes live, push to a branch and open a PR rather than pushing
straight to `main`.

## Schema

```json
{
  "events": {
    "<week_index>": {
      "car": "ferrari_458",
      "track": "monza",
      "layout": "",
      "note": "optional, ignored by the game"
    }
  }
}
```

`week_index` is `floor((unix_timestamp + 259200) / 604800)` — a raw week
counter since the Unix epoch, shifted 3 days (259200 sec) so boundaries
land on **Monday 00:00 UTC** instead of the raw-epoch default of Thursday
(Jan 1 1970 was a Thursday). Matches the game's own `GlobalEvent.week_index()`
exactly — see `WEEK_OFFSET_SEC` there and in `validate.py` here. If you
ever need this by hand, `add_week.py --date YYYY-MM-DD` computes it for you.
