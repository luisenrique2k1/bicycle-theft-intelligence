{{ config(materialized='table') }}

select
    crime_id,
    persistent_id,
    crime_month,
    street_id,
    latitude,
    longitude,
    location_type,
    location_subtype,
    outcome_category,
    outcome_month,
    source_file
from {{ ref('stg_crimes') }}
