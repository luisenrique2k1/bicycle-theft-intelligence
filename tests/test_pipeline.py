from pathlib import Path

import duckdb
import pytest

from pipeline.build import DataQualityError, build, run_checks

FIXTURES = Path(__file__).parent / "fixtures" / "raw"


@pytest.fixture()
def con(tmp_path):
    connection = build(FIXTURES, str(tmp_path / "t.duckdb"), None)
    yield connection
    connection.close()


def test_overlapping_tiles_are_deduplicated(con):
    # 7 raw records, crime 1004 appears in both tiles -> 6 unique crimes
    assert con.execute("select count(*) from raw_crimes").fetchone()[0] == 7
    assert con.execute("select count(*) from fct_bike_theft").fetchone()[0] == 6


def test_blank_persistent_id_becomes_null_not_a_key(con):
    blanks = con.execute("select count(*) from stg_crimes where persistent_id = ''").fetchone()[0]
    assert blanks == 0
    assert con.execute("select count(*) from stg_crimes where persistent_id is null").fetchone()[0] == 3


def test_missing_outcome_is_labelled(con):
    n = con.execute("select thefts from mart_outcomes where outcome_category = 'No outcome recorded yet'").fetchone()[0]
    assert n == 4


def test_hotspot_ranking(con):
    top = con.execute("select street_name, thefts from mart_street_hotspots where hotspot_rank = 1 order by 1").fetchall()
    assert top == [("On or near Bank Station", 2), ("On or near Cycle Park", 2)]


def test_rebuild_is_idempotent(tmp_path):
    db = str(tmp_path / "t.duckdb")
    c1 = build(FIXTURES, db, None)
    snap1 = {t: c1.execute(f"select * from {t} order by all").fetchall()
             for t in ["stg_crimes", "fct_bike_theft", "mart_street_hotspots", "mart_outcomes"]}
    c1.close()
    c2 = build(FIXTURES, db, None)
    snap2 = {t: c2.execute(f"select * from {t} order by all").fetchall() for t in snap1}
    assert snap1 == snap2


def test_quality_check_catches_bad_data(con):
    con.execute("update stg_crimes set latitude = 10.0 where crime_id = 1001")
    with pytest.raises(DataQualityError):
        run_checks(con)


def test_report_is_written(con, tmp_path):
    from pipeline.report import write_report

    project_root = Path(__file__).resolve().parents[1]
    map_metadata = project_root / "reports" / "london_theft_map_bounds.json"
    map_svg = project_root / "reports" / "london_basemap_georeferenced.svg"

    if not map_metadata.exists() or not map_svg.exists():
        pytest.skip("London map assets are not available in this environment")

    report_path = tmp_path / "report.html"
    write_report(con, report_path)

    html = report_path.read_text(encoding="utf-8")
    assert "not the same as risk" in html and "Bank Station" in html
