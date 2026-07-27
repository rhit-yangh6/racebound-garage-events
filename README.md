# racebound-garage-events

Weekly Global Event picks for RaceBound Garage, fetched at runtime from
`global_events.json`. A week with no entry here just falls back to the
game's own deterministic pick — nothing needs to be filled in ahead of time.

## Adding a week

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

`week_index` is `floor(unix_timestamp / 604800)` — a raw week counter since
the Unix epoch, matching the game's own `GlobalEvent.week_index()`.
