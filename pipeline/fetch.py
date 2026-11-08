"""Fetch street-level bicycle-theft crimes from data.police.uk.

Raw responses are written to disk byte-for-byte as returned (no re-serialising),
one file per (month, tile). A manifest records what was fetched and a checksum.
Re-runs skip files that already exist, so the fetch is idempotent.

Usage:
    python -m pipeline.fetch --months 2025-09 [--force]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://data.police.uk/api/crimes-street/bicycle-theft"
AVAILABLE_DATES_API = "https://data.police.uk/api/crimes-street-dates"
RAW_DIR = Path("data/raw")
MANIFEST = Path("data/manifest.csv")
MANIFEST_FIELDS = ["month", "tile", "lat", "lng", "url", "http_status", "bytes", "sha256", "fetched_at_utc"]
USER_AGENT = "bike-theft-pipeline/0.1 (learning project)"

# Each tile returns crimes within ~1 mile of its centre, so tiles are spaced
# ~2 km apart to overlap slightly: no gaps, and overlaps are removed in staging.
# Name -> (lat, lng). Central London first, then places the author rides.
TILES: dict[str, tuple[float, float]] = {
    "london_centre": (51.5074, -0.1278),
    "london_city": (51.5155, -0.0922),
    "london_shoreditch": (51.5260, -0.0780),
    "london_kings_cross": (51.5308, -0.1238),
    "london_camden": (51.5390, -0.1426),
    "london_westminster": (51.4975, -0.1357),
    "london_southbank": (51.5045, -0.0865),
    "london_brixton": (51.4613, -0.1156),
    "london_hackney": (51.5450, -0.0553),
    "london_greenwich": (51.4826, 0.0077),
    "brighton": (50.8225, -0.1372),
    "guildford": (51.2362, -0.5704),
}

def get_latest_available_month() -> str:
    """Return the latest published UK Police street-crime month."""
    response = requests.get(AVAILABLE_DATES_API, timeout=30)
    response.raise_for_status()

    months = [
        item["date"]
        for item in response.json()
        if isinstance(item, dict) and "date" in item
    ]

    if not months:
        raise RuntimeError("Police API returned no available crime-data months")

    latest = max(months)
    datetime.strptime(latest, "%Y-%m")

    return latest

def tile_path(month: str, tile: str) -> Path:
    return RAW_DIR / month / f"{tile}.json"


def fetch_tile(session: requests.Session, month: str, lat: float, lng: float, retries: int = 4) -> requests.Response:
    params = {"date": month, "lat": lat, "lng": lng}
    for attempt in range(retries):
        resp = session.get(API, params=params, timeout=60)
        if resp.status_code == 200:
            return resp
        if resp.status_code in (429, 502, 503, 504):
            time.sleep(2 ** attempt)  # polite exponential backoff
            continue
        if resp.status_code == 404:
            return resp  # month not published yet: record it, don't crash
        resp.raise_for_status()
    resp.raise_for_status()
    return resp


def append_manifest(row: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    new = not MANIFEST.exists()
    with MANIFEST.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def run(months: list[str], force: bool = False, pause: float = 0.2) -> int:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    fetched = 0
    for month in months:
        for tile, (lat, lng) in TILES.items():
            path = tile_path(month, tile)
            if path.exists() and not force:
                print(f"skip  {month} {tile} (already on disk)")
                continue
            resp = fetch_tile(session, month, lat, lng)
            if resp.status_code != 200:
                print(f"WARN  {month} {tile}: HTTP {resp.status_code}, nothing written", file=sys.stderr)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(resp.content)  # exactly as returned
            append_manifest({
                "month": month, "tile": tile, "lat": lat, "lng": lng,
                "url": resp.url, "http_status": resp.status_code,
                "bytes": len(resp.content),
                "sha256": hashlib.sha256(resp.content).hexdigest(),
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            fetched += 1
            print(f"saved {month} {tile} ({len(resp.content)} bytes)")
            time.sleep(pause)  # well under the 15 req/s limit
    return fetched


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)

    group = p.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--months",
        nargs="+",
        help="Specific months to fetch, e.g. 2025-09",
    )

    group.add_argument(
        "--latest",
        action="store_true",
        help="Automatically fetch the latest available crime-data month",
    )

    p.add_argument(
        "--force",
        action="store_true",
        help="Re-download files already on disk",
    )

    args = p.parse_args()

    if args.latest:
        months = [get_latest_available_month()]
        print(f"Latest available month: {months[0]}")
    else:
        months = args.months

    for month in months:
        datetime.strptime(month, "%Y-%m")

    n = run(months, force=args.force)
    print(f"done: {n} new files")


if __name__ == "__main__":
    main()
