{{ config(materialized='table') }}

select
    crime_month,
    count(*) as total_thefts,
    count(distinct street_id) as affected_streets,
    count(*) filter (
        where outcome_category is not null
    ) as crimes_with_outcome
from {{ ref('fct_bicycle_thefts') }}
group by crime_month
order by crime_month
