{{ config(materialized='table') }}

select
    street_id,
    min(street_name) as street_name,
    count(*) as recorded_thefts
from {{ ref('stg_crimes') }}
group by street_id
