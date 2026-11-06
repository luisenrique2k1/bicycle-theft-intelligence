"""Render a small, dependency-free static HTML report from the marts."""
from __future__ import annotations

from html import escape
from pathlib import Path

import duckdb

CAVEAT = (
    "Recorded thefts are not the same as risk. Many bicycle thefts are never reported, "
    "locations are deliberately approximated by the police (\"on or near\"), and busy places "
    "have more bikes to steal. Read this as where thefts are <em>recorded</em>, not a safety rating."
)


def _bar_svg(rows: list[tuple[str, int]]) -> str:
    if not rows:
        return "<p>No data.</p>"
    top = max(v for _, v in rows) or 1
    h = 26
    out = [f'<svg role="img" aria-label="Thefts by street" width="720" height="{h * len(rows) + 4}">']
    for i, (label, v) in enumerate(rows):
        w = int(360 * v / top)
        y = i * h
        out.append(f'<text x="0" y="{y + 17}" font-size="13">{escape(label[:38])}</text>')
        out.append(f'<rect x="270" y="{y + 4}" width="{w}" height="16" fill="#1f6feb"/>')
        out.append(f'<text x="{276 + w}" y="{y + 17}" font-size="13">{v}</text>')
    out.append("</svg>")
    return "".join(out)


def write_report(con: duckdb.DuckDBPyConnection, path: Path, top_n: int = 15) -> None:
    total, first, last = con.execute(
        "select count(*), min(month_start), max(month_start) from fct_bike_theft"
    ).fetchone()
    hotspots = con.execute(
        "select hotspot_rank, street_name, thefts, pct_of_all_thefts, hotspot_score "
        "from mart_street_hotspots order by hotspot_rank, street_name limit ?", [top_n]
    ).fetchall()
    trend = con.execute("select month_label, thefts from mart_monthly_trend").fetchall()
    outcomes = con.execute("select outcome_category, thefts, pct from mart_outcomes").fetchall()

    def table(head, rows):
        th = "".join(f"<th>{escape(h)}</th>" for h in head)
        tr = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"

    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Where bike thefts are recorded</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 1rem}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:.3rem .5rem;text-align:left}}
.note{{background:#fff8e1;border-left:4px solid #f0b429;padding:.6rem 1rem}}</style>
<h1>Where bike thefts are recorded</h1>
<p>{total} recorded bicycle thefts across the sampled London and South East areas, {first} to {last}.</p>
<p class="note">{CAVEAT}</p>
<h2>Top {top_n} streets</h2>{_bar_svg([(r[1], r[2]) for r in hotspots])}
{table(["Rank", "Street (approximate)", "Thefts", "% of all", "Score (0-1)"], hotspots)}
<h2>By month</h2>{table(["Month", "Thefts"], trend)}
<h2>What happened next</h2>{table(["Outcome", "Thefts", "%"], outcomes)}
<p><small>Source: data.police.uk, Open Government Licence v3.0.</small></p></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
