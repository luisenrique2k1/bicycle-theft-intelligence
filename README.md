# Where are bikes stolen? A small data pipeline on UK police data

## What I built and who for

A pipeline that pulls street-level **bicycle theft** records from the data.police.uk API for
central London and a few places I ride (Brighton, Guildford), keeps the raw responses, cleans
them into a small DuckDB model, and produces a one-page HTML report ranking streets by recorded thefts.

It is for **cyclists and cycling clubs deciding where to lock up**. It is a sampling aid, not a safety rating:
recorded theft is not the same as risk (many thefts go unreported, locations are deliberately approximate,
and busy places have more bikes to steal). The report says this at the top.

## The data

- Source: [data.police.uk street-level crimes API](https://data.police.uk/docs/method/crime-street/), category `bicycle-theft`.
- Licence: Open Government Licence v3.0. No API key needed. Rate limit ~15 requests/second (I use ~5).
- Each call returns crimes within ~1 mile of a point for one month. I use a hand-picked list of tile centres
  (`pipeline/fetch.py`, `TILES`) that overlap slightly so there are no gaps.
- Quirks I handle: the same crime appears in overlapping tiles; `persistent_id` is often blank so I key on `id`;
  `outcome_status` is null until an outcome is recorded; street names/locations are anonymised ("On or near ...").
- Raw responses are committed unchanged in `data/raw/<YYYY-MM>/<tile>.json`, with `data/manifest.csv` (URL, time, checksum).

## How it works

```
fetch.py -> data/raw/*.json (byte-for-byte)  ->  DuckDB:
  01_raw.sql      raw_crimes            (as received)
  02_staging.sql  stg_crimes            (types, trimmed, blanks -> NULL, deduplicated on id)
  03_model.sql    dim_month, dim_street, fct_bike_theft, fct_outcome
  04_marts.sql    mart_street_hotspots (rank + 0-1 score), mart_monthly_trend, mart_outcomes
  90_checks.sql   data-quality checks: the build fails if any check finds bad rows
-> reports/report.html
```

Re-running is safe: the fetch skips files already on disk, and the build is a full `CREATE OR REPLACE` rebuild from raw,
so repeated runs give identical tables (there is a test for this).

## How to run it

Needs Python 3.10+ and bash. No Docker, no credentials.

```bash
./run.sh all                       # tests, then build from the committed raw data -> reports/report.html
./run.sh fetch 2025-09             # optional: download more months (needs internet)
./run.sh test                      # tests only; they use synthetic fixtures in tests/fixtures
```

## What I would do next

- Add more months so the trend is meaningful, and compare like-for-like months across years.
- Join the later-arriving outcomes (the API's outcomes endpoint) rather than relying on the street-level snapshot.
- Normalise by something like cycle-parking counts or footfall so busy places are not unfairly flagged.
- Schedule the fetch using the `crime-last-updated` endpoint and only load new months.
- Add a map view.

## Where AI helped

<!-- TODO (Luis): replace this with your own honest account before submitting. -->
Claude (an AI assistant) drafted the first version of the fetcher, the SQL layers, the checks, the tests and this README
structure, working from the project brief I gave it. It was not able to reach the police API from its environment,
so it tested the pipeline against synthetic fixtures I then used to check the real data.

**Kept:** _(what you kept as written, e.g. the layered SQL structure, and why)_
**Rejected:** _(what you decided against, e.g. using `persistent_id` as the key, and why)_
**Changed:** _(what you edited after reading the code, and what you learned from it)_

Be ready to explain every line in the video call.
