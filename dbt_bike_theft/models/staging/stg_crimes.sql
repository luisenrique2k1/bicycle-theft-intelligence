{{ config(materialized='table') }}

with cleaned as (

    select
        id as crime_id,
        persistent_id,
        category,
        location_type,
        location_subtype,

        try_cast(latitude as double) as latitude,
        try_cast(longitude as double) as longitude,

        street_id,
        trim(street_name) as street_name,

        try_cast(month || '-01' as date) as crime_month,

        nullif(trim(outcome_category), '') as outcome_category,
        try_cast(outcome_date || '-01' as date) as outcome_month,

        source_month_dir,
        source_file

    from {{ ref('raw_crimes') }}

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by crime_id
            order by source_file
        ) as row_num

    from cleaned

)

select * exclude (row_num)
from deduplicated
where row_num = 1
