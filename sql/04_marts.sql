-- Marts: what the report reads.
create or replace table mart_street_hotspots as
with per_street as (
    select
        s.street_id,
        coalesce(s.street_name, 'Unknown street') as street_name,
        s.centre_latitude, s.centre_longitude,
        count(*) as thefts
    from fct_bike_theft f
    join dim_street s using (street_id)
    group by all
)
select
    *,
    round(100.0 * thefts / sum(thefts) over (), 2)                 as pct_of_all_thefts,
    rank() over (order by thefts desc)                             as hotspot_rank,
    -- light scoring: percentile of theft count among streets that had any theft
    round(percent_rank() over (order by thefts), 2)                 as relative_count_percentile
from per_street;

create or replace table mart_monthly_trend as
select m.month_start, m.month_label, count(f.crime_id) as thefts
from dim_month m
left join fct_bike_theft f using (month_start)
group by all
order by m.month_start;

create or replace table mart_outcomes as
select
    outcome_category,
    count(*) as thefts,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as pct
from fct_outcome
group by outcome_category
order by thefts desc;
-- Advanced monthly trend analytics
create or replace table mart_advanced_trends as
with monthly as (
    select
        month_start,
        thefts,
        avg(thefts) over (
            order by month_start
            rows between 2 preceding and current row
        ) as rolling_3m,
        avg(thefts) over (
            order by month_start
            rows between 11 preceding and current row
        ) as rolling_12m,
        lag(thefts) over (
            order by month_start
        ) as previous_month,
        lag(thefts, 12) over (
            order by month_start
        ) as same_month_last_year
    from mart_monthly_trend
)
select
    month_start,
    thefts,
    round(rolling_3m, 1) as rolling_3m,
    round(rolling_12m, 1) as rolling_12m,
    thefts - previous_month as mom_change,
    round(
        100.0 * (thefts - previous_month)
        / nullif(previous_month, 0),
        1
    ) as mom_change_pct,
    thefts - same_month_last_year as yoy_change,
    round(
        100.0 * (thefts - same_month_last_year)
        / nullif(same_month_last_year, 0),
        1
    ) as yoy_change_pct
from monthly
order by month_start;