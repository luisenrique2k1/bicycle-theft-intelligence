"""Generate a standalone, interactive bicycle theft dashboard from DuckDB marts.

No frontend dependencies or external assets are required.
"""
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
import json

import duckdb

CAVEAT = (
    'Recorded thefts are not the same as risk. Police locations are approximate '
    '("on or near"), some thefts are unreported, and cycling exposure is unknown. '
    'The collection points sample London and South East England; they do not '
    'provide complete geographic coverage.'
)


def _json(value: object) -> str:
    # Prevent embedded JSON from prematurely closing the script element.
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def _month_label(value: date | None) -> str:
    return value.strftime('%B %Y') if value else 'Unknown'


def write_report(con: duckdb.DuckDBPyConnection, path: Path, top_n: int = 15) -> None:
    total, first, last = con.execute(
        'SELECT count(*), min(month_start), max(month_start) FROM fct_bike_theft'
    ).fetchone()
    raw_count = con.execute('SELECT count(*) FROM raw_crimes').fetchone()[0]
    duplicate_count = raw_count - total
    mapped_count = con.execute('SELECT coalesce(sum(thefts), 0) FROM mart_street_hotspots').fetchone()[0]
    trend = [dict(month=str(d), label=label, thefts=n) for d, label, n in con.execute(
        'SELECT month_start, month_label, thefts FROM mart_monthly_trend ORDER BY month_start'
    ).fetchall()]
    advanced_trends = [
    dict(
        month=str(month),
        thefts=thefts,
        rolling_3m=rolling_3m,
        rolling_12m=rolling_12m,
        yoy_change_pct=yoy_change_pct
    )
    for month, thefts, rolling_3m, rolling_12m, yoy_change_pct
    in con.execute("""
        SELECT
            month_start,
            thefts,
            rolling_3m,
            rolling_12m,
            yoy_change_pct
        FROM mart_advanced_trends
        ORDER BY month_start
    """).fetchall()
    ]
    # October-to-September reporting years, derived from the monthly mart.
    reporting_years = {}
    for row in trend:
        year, month = map(int, row['month'].split('-')[:2])
        start_year = year if month >= 10 else year - 1
        key = f'{start_year}–{start_year + 1}'
        reporting_years.setdefault(key, {'label': key, 'total': 0, 'months': 0})
        reporting_years[key]['total'] += row['thefts']
        reporting_years[key]['months'] += 1
    annual = list(reporting_years.values())
    previous_total = None
    for item in annual:
        item['change_pct'] = (
            round(100 * (item['total'] - previous_total) / previous_total, 1)
            if previous_total else None
        )
        previous_total = item['total']
    hotspots = [dict(rank=rank, street_id=street_id, street=street, thefts=n, pct=pct,
                     latitude=lat, longitude=lon) for rank, street_id, street, n, pct, lat, lon in con.execute(
        'SELECT hotspot_rank, street_id, street_name, thefts, pct_of_all_thefts, '
        'centre_latitude, centre_longitude FROM mart_street_hotspots '
        'ORDER BY hotspot_rank, street_name, street_id LIMIT ?', [top_n]
    ).fetchall()]
    outcomes = [dict(category=category, thefts=n, pct=pct) for category, n, pct in con.execute(
        'SELECT outcome_category, thefts, pct FROM mart_outcomes ORDER BY thefts DESC'
    ).fetchall()]
    peak = max(trend, key=lambda x: x['thefts']) if trend else None
    top_location = hotspots[0] if hotspots else None
    no_suspect = next((x for x in outcomes if x['category'] == 'Investigation complete; no suspect identified'), None)
    period = f'{_month_label(first)} – {_month_label(last)}'
    # Dataset is written as JSON, and HTML is static: reviewers can open it offline.
    payload = _json(dict(
        trend=trend,
        advanced_trends=advanced_trends,
        annual=annual,
        hotspots=hotspots,
        outcomes=outcomes
    ))
    cards = [
        ('Unique recorded thefts', f'{total:,}', 'Deduplicated police records'),
        ('Duplicate occurrences', f'{duplicate_count:,}', f'From {raw_count:,} raw records'),
        ('Highest-count month', peak['label'] if peak else '—', f"{peak['thefts']:,} thefts" if peak else 'No data'),
        ('No suspect identified', f"{no_suspect['pct']:.1f}%" if no_suspect else '—',
         f"{no_suspect['thefts']:,} records" if no_suspect else 'No data'),
    ]
    cards_html = ''.join(
        f'<article class="metric"><div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div><div class="metric-note">{escape(note)}</div></article>'
        for label, value, note in cards
    )
    html = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bicycle Theft Intelligence | Data Engineering Portfolio</title>
<style>
:root{color-scheme:light;--ink:#15243b;--muted:#63748b;--line:#dce5ee;--blue:#2563eb;--navy:#0c1c35;--bg:#f4f7fb;--white:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:inherit}nav{background:var(--navy);color:#e8f0ff;padding:15px max(20px,calc((100vw - 1180px)/2));display:flex;gap:20px;align-items:center;flex-wrap:wrap}
nav strong{margin-right:auto;letter-spacing:.02em}nav a{text-decoration:none;font-size:13px;color:#c9d8ed}nav a:hover{text-decoration:underline}
main{max-width:1180px;margin:auto;padding:32px 20px 70px}.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:11px;font-weight:800;color:#4163a5}
h1{font-size:clamp(29px,4vw,45px);line-height:1.13;margin:8px 0 10px;letter-spacing:-.035em}.subtitle{color:var(--muted);margin:0 0 24px}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.metric,.panel{background:var(--white);border:1px solid var(--line);border-radius:14px;box-shadow:0 5px 20px #15243b08}
.metric{padding:20px}.metric-label{font-size:12px;font-weight:650;color:var(--muted)}.metric-value{font-size:clamp(20px,2.4vw,31px);font-weight:780;letter-spacing:-.03em;margin:8px 0}.metric-note{font-size:12px;color:var(--muted)}
.section{margin-top:31px}.section h2{font-size:22px;letter-spacing:-.02em;margin:0 0 12px}.section>p{color:var(--muted);margin:0 0 16px}.panel{padding:22px}
.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.grid-even{grid-template-columns:1fr 1fr}.panel h3{font-size:16px;margin:0 0 12px}.small{font-size:12px;color:var(--muted)}
.chart{width:100%;overflow-x:auto}.chart svg{display:block;width:100%;min-width:500px;height:auto}.axis{fill:#65758a;font-size:11px}.line{fill:none;stroke:var(--blue);stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.point{fill:var(--white);stroke:var(--blue);stroke-width:2.5}
.bar-row{display:grid;grid-template-columns:minmax(115px,1fr) 2fr 45px;gap:10px;align-items:center;margin:10px 0;font-size:12px}.bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:12px;background:#e9eff7;border-radius:5px;overflow:hidden}.bar-fill{height:100%;background:linear-gradient(90deg,#2563eb,#60a5fa);border-radius:5px}.bar-count{text-align:right;font-weight:700}
.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;color:var(--muted);font-weight:700;background:#f7f9fc}th,td{padding:10px 12px;border-bottom:1px solid var(--line)}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:10px 0 18px}button{border:1px solid #cbd8e8;border-radius:8px;background:white;color:var(--ink);padding:8px 12px;cursor:pointer;font:inherit;font-size:12px}button.active{background:var(--navy);color:white;border-color:var(--navy)}
.note{border-left:4px solid #e5a33c;background:#fff8e8;border-radius:8px;padding:14px 18px;margin-top:18px;color:#614619}.quality{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.quality>div{padding:15px;background:#f6f9fd;border-radius:10px}.quality strong{display:block;font-size:22px}.quality span{font-size:12px;color:var(--muted)}
.annual-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:16px 0}.annual-card{padding:19px;border:1px solid var(--line);border-radius:12px;background:#f8faff}.annual-card .value{font-size:30px;font-weight:800;letter-spacing:-.04em}.annual-card .delta{font-size:12px;color:var(--muted)}.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:8px 0}.swatch{display:inline-block;width:18px;height:4px;border-radius:3px;vertical-align:middle;margin-right:5px}.chart-label{font-size:12px;color:var(--muted);margin-top:10px}.pill{font-size:11px;color:#176b4c;background:#e8f7ee;border-radius:30px;padding:4px 9px;font-weight:750}.footer{color:var(--muted);font-size:12px;margin-top:32px}
@media(max-width:850px){.annual-grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.grid,.grid-even{grid-template-columns:1fr}}@media(max-width:520px){.metrics{grid-template-columns:1fr}.quality{grid-template-columns:1fr}nav{gap:12px}.panel{padding:16px}}
</style></head><body>
<nav><strong>BICYCLE THEFT INTELLIGENCE</strong><a href="#overview">Overview</a><a href="#trends">Trends</a><a href="#comparison">Year comparison</a><a href="#locations">Locations</a><a href="#outcomes">Outcomes</a><a href="#quality">Data quality</a><a href="#methodology">Methodology</a></nav>
<main><header id="overview"><div class="eyebrow">Data engineering portfolio · Police API / DuckDB / Python / SQL</div>
<h1>Where bicycle thefts are recorded</h1><p class="subtitle">Selected London &amp; South East collection areas · PERIOD_PLACEHOLDER</p></header>
<div class="metrics">CARDS_PLACEHOLDER</div>
<div class="note"><strong>Interpretation:</strong> CAVEAT_PLACEHOLDER</div>
<section class="section" id="trends"><h2>01 · Monthly trends</h2><p>Deduplicated recorded bicycle thefts by reported month. Use the controls to switch between monthly and cumulative totals.</p>
<div class="panel"><div class="controls"><button id="monthly" class="active" type="button" aria-pressed="true">Monthly</button><button id="cumulative" type="button" aria-pressed="false">Cumulative</button></div><div class="chart" id="trend-chart" role="img" aria-label="Monthly theft trend"></div><p class="small">Three annual cycles are included. Apparent seasonal patterns should be interpreted cautiously; counts are not adjusted for cycling exposure.</p></div></section>
<section class="section" id="comparison"><h2>02 · Three-year comparison</h2><p>October–September reporting periods. Compare corresponding months across years; totals are based on the same sampled collection points.</p>
<div class="panel"><h3>Annual recorded thefts</h3><div class="annual-grid" id="annual-cards"></div><h3>Monthly comparison by reporting year</h3><div class="legend" id="comparison-legend"></div><div class="chart" id="comparison-chart" role="img" aria-label="Three reporting years compared by month"></div><p class="small">Each series runs October to September. Year-over-year changes compare the same reporting period.</p></div></section>
<section class="section" id="rolling"><h2>03 · Rolling averages and annual change</h2><p>SQL window functions smooth monthly variation and compare each month with the same month one year earlier.</p><div class="panel"><div class="controls"><button id="mode-count" class="active" type="button" aria-pressed="true">Monthly counts</button><button id="mode-3m" type="button" aria-pressed="false">3-month average</button><button id="mode-12m" type="button" aria-pressed="false">12-month average</button><button id="mode-yoy" type="button" aria-pressed="false">Year-on-year %</button></div><div class="chart" id="advanced-chart" role="img" aria-label="Rolling averages and year-on-year trend"></div><p class="small" id="advanced-note">Rolling averages are trailing windows. The first 2 and 11 months respectively use shorter partial windows.</p></div></section>
<section class="section" id="locations"><h2>04 · Approximate location analysis</h2><p>Highest recorded counts among the sampled Police API locations. These are anonymised street-level reference points, not precise incident coordinates.</p>
<div class="grid"><div class="panel"><h3>Highest-count locations</h3><div id="hotspot-bars"></div></div><div class="panel"><h3>Ranked locations</h3><div class="table-wrap"><table><thead><tr><th>Rank</th><th>Location (approx.)</th><th class="num">Thefts</th><th class="num">Share</th></tr></thead><tbody id="hotspot-table"></tbody></table></div></div></div></section>
<section class="section" id="outcomes"><h2>05 · Investigation outcomes</h2><p>Current outcome category attached to each crime record. These are snapshots, not a full timeline of investigative events.</p>
<div class="grid grid-even"><div class="panel"><h3>Outcome distribution</h3><div id="outcome-bars"></div></div><div class="panel"><h3>All outcome categories</h3><div class="table-wrap"><table><thead><tr><th>Outcome</th><th class="num">Thefts</th><th class="num">Share</th></tr></thead><tbody id="outcome-table"></tbody></table></div></div></div></section>
<section class="section" id="quality"><h2>06 · Data quality &amp; pipeline</h2><p>Traceable transformation from archived API responses into a deduplicated analytical warehouse.</p>
<div class="panel"><div class="quality"><div><strong>RAW_PLACEHOLDER</strong><span>Raw records ingested</span></div><div><strong>DUP_PLACEHOLDER</strong><span>Duplicate occurrences removed</span></div><div><strong>TOTAL_PLACEHOLDER</strong><span>Unique records in fact table</span></div></div><p class="small">Deduplication uses the police crime ID across overlapping geographic collection points. The pipeline runs SQL quality checks before generating this report.</p><p class="small">Location mapping coverage: MAPPED_PLACEHOLDER of TOTAL_PLACEHOLDER fact records represented in the street mart.</p></div></section>
<section class="section" id="methodology"><h2>07 · Methodology &amp; limitations</h2><div class="panel"><p><strong>Source:</strong> UK Police street-level bicycle theft API (<a href="https://data.police.uk/">data.police.uk</a>), Open Government Licence v3.0.</p>
<p><strong>Pipeline:</strong> Archived JSON → DuckDB raw table → typed/deduplicated staging → fact/dimension tables → analytical marts → standalone HTML.</p>
<p><strong>Geographic coverage:</strong> Selected collection points in London and South East England, including Brighton and Guildford. This is <strong>not</strong> a complete count for London or the South East.</p>
<p><strong>Time:</strong> Police data is monthly, not an exact crime timestamp. Dates in the warehouse represent the first day of each reporting month.</p>
<p><strong>Interpretation:</strong> Police street coordinates are approximate. Counts are not exposure-adjusted risk measures, and differences may reflect reporting, coverage and activity. Investigation outcomes can change after collection.</p>
<p><strong>Reproducibility:</strong> The warehouse and this report are rebuilt from the archived raw responses; no live API connection is required to reproduce the saved dataset.</p></div></section>
<div class="footer">Generated from DuckDB · Standalone HTML · No external charting dependencies</div>
</main><script id="report-data" type="application/json">DATA_PLACEHOLDER</script>
<script>
(()=>{'use strict';
const data=JSON.parse(document.getElementById('report-data').textContent);
const $=id=>document.getElementById(id);
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n};
const fmt=n=>Number(n).toLocaleString('en-GB');
function renderBars(id,rows,labelKey,maxRows){const root=$(id);root.replaceChildren();const subset=rows.slice(0,maxRows),max=Math.max(1,...subset.map(r=>r.thefts));for(const r of subset){const row=el('div','bar-row');const label=el('span','bar-label',r[labelKey]);label.title=r[labelKey];const track=el('div','bar-track');const fill=el('div','bar-fill');fill.style.width=(100*r.thefts/max)+'%';track.append(fill);row.append(label,track,el('span','bar-count',fmt(r.thefts)));root.append(row)}}
function renderTable(id,rows,fields){const root=$(id);root.replaceChildren();for(const r of rows){const tr=el('tr');for(const [key,format,numeric] of fields){const td=el('td',numeric?'num':'',format?format(r[key]):r[key]);tr.append(td)}root.append(tr)}}
renderBars('hotspot-bars',data.hotspots,'street',10);
renderTable('hotspot-table',data.hotspots,[['rank',null,false],['street',null,false],['thefts',fmt,true],['pct',v=>Number(v).toFixed(2)+'%',true]]);
renderBars('outcome-bars',data.outcomes,'category',6);
renderTable('outcome-table',data.outcomes,[['category',null,false],['thefts',fmt,true],['pct',v=>Number(v).toFixed(1)+'%',true]]);
function trend(cumulative){const rows=data.trend;const values=[];let sum=0;for(const r of rows){sum+=r.thefts;values.push(cumulative?sum:r.thefts)}const root=$('trend-chart');root.replaceChildren();if(!rows.length){root.textContent='No monthly data.';return}const W=920,H=310,L=54,R=20,T=18,B=50,innerW=W-L-R,innerH=H-T-B,max=Math.max(1,...values)*1.12;
const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('aria-label',cumulative?'Cumulative thefts by month':'Recorded thefts by month');
const node=(tag,attrs,content)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(content!==undefined)n.textContent=String(content);svg.append(n);return n};
const x=i=>L+(rows.length===1?innerW/2:i*innerW/(rows.length-1));const y=v=>T+innerH-v/max*innerH;
for(let i=0;i<=4;i++){const val=max*i/4,py=y(val);node('line',{x1:L,y1:py,x2:W-R,y2:py,stroke:'#e5ecf4'});node('text',{x:L-10,y:py+4,'text-anchor':'end',class:'axis'},fmt(Math.round(val)))}
rows.forEach((r,i)=>{if(i%3===0||i===rows.length-1){const d=r.month;const label=d.slice(5,7)+'/'+d.slice(2,4);node('text',{x:x(i),y:H-19,'text-anchor':'middle',class:'axis'},label)}});
node('polyline',{points:values.map((v,i)=>`${x(i)},${y(v)}`).join(' '),class:'line'});
values.forEach((v,i)=>{const p=node('circle',{cx:x(i),cy:y(v),r:4,class:'point'});const title=document.createElementNS(ns,'title');title.textContent=`${rows[i].label}: ${fmt(v)}`;p.append(title)});
root.append(svg)}
function setMode(cumulative){$('monthly').classList.toggle('active',!cumulative);$('cumulative').classList.toggle('active',cumulative);$('monthly').setAttribute('aria-pressed',String(!cumulative));$('cumulative').setAttribute('aria-pressed',String(cumulative));trend(cumulative)}
$('monthly').addEventListener('click',()=>setMode(false));$('cumulative').addEventListener('click',()=>setMode(true));setMode(false);

// Generic SVG line chart for annual comparisons and advanced analytics.
function lineChart(id, series, labels, options={}) {
 const root=$(id);root.replaceChildren();
 if(!labels.length){root.textContent='No data available';return;}
 const W=920,H=320,L=65,R=20,T=24,B=55,iw=W-L-R,ih=H-T-B;
 const all=series.flatMap(s=>s.values.filter(v=>v!==null&&Number.isFinite(v)));
 let low=options.zeroBased===false?Math.min(0,...all):0;
 let high=Math.max(1,...all);if(options.zeroBased===false){low=Math.min(0,...all);high=Math.max(0,...all)}
 if(high===low)high=low+1;const pad=(high-low)*.08;high+=pad;if(low<0)low-=pad;
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('role','img');
 const add=(tag,attrs,content,parent=svg)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(content!==undefined)n.textContent=String(content);parent.append(n);return n};
 const x=i=>L+(labels.length===1?iw/2:i*iw/(labels.length-1)),y=v=>T+(high-v)/(high-low)*ih;
 for(let i=0;i<=4;i++){const val=low+(high-low)*i/4;add('line',{x1:L,y1:y(val),x2:W-R,y2:y(val),stroke:'#e5ecf4'});add('text',{x:L-9,y:y(val)+4,'text-anchor':'end',class:'axis'},options.percent?val.toFixed(0)+'%':fmt(Math.round(val)))}
 const interval=labels.length>20?3:1;
 labels.forEach((label,i)=>{if(i%interval===0||i===labels.length-1)add('text',{x:x(i),y:H-17,'text-anchor':'middle',class:'axis'},label)});
 for(const s of series){let segment=[];const flush=()=>{if(segment.length>1)add('polyline',{points:segment.join(' '),fill:'none',stroke:s.color,'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round'});segment=[]};
 s.values.forEach((v,i)=>{if(v===null||!Number.isFinite(v)){flush();return;}segment.push(`${x(i)},${y(v)}`);const dot=add('circle',{cx:x(i),cy:y(v),r:3.4,fill:'#fff',stroke:s.color,'stroke-width':2});add('title',{},`${s.name} · ${labels[i]}: ${options.percent?v.toFixed(1)+'%':fmt(v)}`,dot)});flush()}
 root.append(svg);
}
const annualRoot=$('annual-cards');
for(const a of data.annual){const card=el('article','annual-card');card.append(el('div','small',a.label),el('div','value',fmt(a.total)),el('div','delta',a.change_pct===null?'Baseline reporting year':`${a.change_pct>0?'+':''}${a.change_pct}% versus previous year`));annualRoot.append(card)}
const yearColors=['#2563eb','#f59e0b','#16a085','#a855f7'];
const annualLabels=['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep'];
const groups=new Map();
for(const r of data.trend){const [year,month]=r.month.split('-').map(Number);const start=month>=10?year:year-1;const key=`${start}–${start+1}`;if(!groups.has(key))groups.set(key,Array(12).fill(null));groups.get(key)[(month+2)%12]=r.thefts}
const comparisonSeries=[...groups.entries()].map(([name,values],i)=>({name,values,color:yearColors[i%yearColors.length]}));
for(const s of comparisonSeries){const span=el('span');const swatch=el('span','swatch');swatch.style.background=s.color;span.append(swatch,document.createTextNode(s.name));$('comparison-legend').append(span)}
lineChart('comparison-chart',comparisonSeries,annualLabels);
const advancedModes={
 'mode-count':{key:'thefts',name:'Monthly recorded thefts',note:'Monthly counts of unique police records in the sampled areas.'},
 'mode-3m':{key:'rolling_3m',name:'3-month rolling average',note:'Trailing three-month average. The first two points use partial windows.'},
 'mode-12m':{key:'rolling_12m',name:'12-month rolling average',note:'Trailing twelve-month average. The first eleven points use partial windows.'},
 'mode-yoy':{key:'yoy_change_pct',name:'Year-on-year change',note:'Percentage change versus the same month a year earlier. The first twelve months have no comparison.'}
};
function showAdvanced(mode){const spec=advancedModes[mode];for(const id of Object.keys(advancedModes)){$(id).classList.toggle('active',id===mode);$(id).setAttribute('aria-pressed',String(id===mode))}
 const rows=data.advanced_trends,labels=rows.map(r=>r.month.slice(5,7)+'/'+r.month.slice(2,4));
 lineChart('advanced-chart',[{name:spec.name,color:mode==='mode-yoy'?'#b45309':'#2563eb',values:rows.map(r=>r[spec.key]===null?null:Number(r[spec.key]))}],labels,{percent:mode==='mode-yoy',zeroBased:mode!=='mode-yoy'});
 $('advanced-note').textContent=spec.note;
}
for(const id of Object.keys(advancedModes))$(id).addEventListener('click',()=>showAdvanced(id));showAdvanced('mode-count');

})();
</script></body></html>'''
    html = (html.replace('PERIOD_PLACEHOLDER', escape(period))
            .replace('CARDS_PLACEHOLDER', cards_html)
            .replace('CAVEAT_PLACEHOLDER', escape(CAVEAT))
            .replace('RAW_PLACEHOLDER', f'{raw_count:,}')
            .replace('DUP_PLACEHOLDER', f'{duplicate_count:,}')
            .replace('TOTAL_PLACEHOLDER', f'{total:,}')
            .replace('MAPPED_PLACEHOLDER', f'{mapped_count:,}')
            .replace('DATA_PLACEHOLDER', payload))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
