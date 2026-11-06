"""Build the DuckDB warehouse from archived raw JSON, run quality checks, write the report.

Usage:
    python -m pipeline.build [--raw data/raw] [--db warehouse.duckdb] [--report reports/report.html]

The build is a full rebuild from the raw files using CREATE OR REPLACE, so running it
twice gives identical tables (idempotent by construction; see tests/test_pipeline.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

from pipeline.report import write_report

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
LAYERS = ["01_raw.sql", "02_staging.sql", "03_model.sql", "04_marts.sql"]


class DataQualityError(Exception):
    pass


def run_checks(con: duckdb.DuckDBPyConnection) -> list[tuple[str, int]]:
    results = con.execute((SQL_DIR / "90_checks.sql").read_text()).fetchall()
    failed = [(name, n) for name, n in results if n > 0]
    for name, n in results:
        print(f"  {'FAIL' if n else 'ok  '} {name}" + (f" ({n} rows)" if n else ""))
    if failed:
        raise DataQualityError(f"{len(failed)} data-quality check(s) failed: {[f[0] for f in failed]}")
    return results


def build(raw_dir: Path, db_path: str, report_path: Path | None) -> duckdb.DuckDBPyConnection:
    files = sorted(Path(raw_dir).glob("*/*.json"))
    if not files:
        sys.exit(f"No raw files found in {raw_dir}/<YYYY-MM>/*.json. Run: ./run.sh fetch")
    con = duckdb.connect(db_path)
    glob = str(Path(raw_dir) / "*" / "*.json")
    for name in LAYERS:
        sql = (SQL_DIR / name).read_text().replace("{raw_glob}", glob)
        con.execute(sql)
        print(f"ran {name}")
    print("quality checks:")
    run_checks(con)
    if report_path:
        write_report(con, report_path)
        print(f"report written to {report_path}")
    return con


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", default="data/raw")
    p.add_argument("--db", default="warehouse.duckdb")
    p.add_argument("--report", default="reports/report.html")
    a = p.parse_args()
    build(Path(a.raw), a.db, Path(a.report))


if __name__ == "__main__":
    main()
