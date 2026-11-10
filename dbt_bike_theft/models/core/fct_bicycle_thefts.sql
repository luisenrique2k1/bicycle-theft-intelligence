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
    source_file,

    case
        when regexp_extract(
            source_file, '[^/]+\.json$'
        ) = 'brighton.json'
            then 'Brighton'

        when regexp_extract(
            source_file, '[^/]+\.json$'
        ) = 'guildford.json'
            then 'Guildford'

        when regexp_extract(
            source_file, '[^/]+\.json$'
        ) like 'london_%'
            then 'London'

        else 'Other'
    end as collection_area

from {{ ref('stg_crimes') }}
