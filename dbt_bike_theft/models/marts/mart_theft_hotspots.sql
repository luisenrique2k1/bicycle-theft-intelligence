{{ config(materialized='table') }}

select
    d.street_id,
    d.street_name,
    count(*) as total_thefts,
    count(distinct f.crime_month) as months_with_thefts,
    min(f.crime_month) as first_recorded_month,
    max(f.crime_month) as latest_recorded_month,
    round(avg(f.latitude), 5) as latitude,
    round(avg(f.longitude), 5) as longitude
from {{ ref('fct_bicycle_thefts') }} f
inner join {{ ref('dim_streets') }} d
    on f.street_id = d.street_id
group by
    d.street_id,
    d.street_name
