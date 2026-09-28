# SentinelGraph

Evidence-first investigation console linking insider access events to financial transactions. Built for a synthetic bank scenario with deterministic seed data.

All data is synthetic. Not for real financial decisions.

## Setup

```
python scripts/setup.py
```

## Run

```
python scripts/reset_demo.py
python scripts/dev.py
```

## Verify

```
python scripts/verify.py --cp 0
```

## Reset

```
python scripts/reset_demo.py
```

Rebuilds the database from seed files through the ingestion pipeline.

## Known limits

- Single SQLite file, not suitable for concurrent multi-user production use.
- Three demo users with a role header, no real authentication.
- Synthetic data only.
