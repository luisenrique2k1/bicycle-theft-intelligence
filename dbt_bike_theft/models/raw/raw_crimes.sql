
{{ config(materialized='table') }}

select
    category,
    location_type,
    location.latitude        as latitude,
    location.longitude       as longitude,
    location.street.id       as street_id,
    location.street.name     as street_name,
    context,
    outcome_status.category  as outcome_category,
    outcome_status.date      as outcome_date,
    persistent_id,
    id,
    location_subtype,
    month,
    regexp_extract(filename, '([^/]+)/[^/]+$', 1) as source_month_dir,
    filename as source_file
from read_json(
    'data/raw/*/*.json',
    format = 'array',
    filename = true,
    columns = {
        category: 'VARCHAR',
        location_type: 'VARCHAR',
        location: 'STRUCT(latitude VARCHAR, longitude VARCHAR, street STRUCT(id BIGINT, name VARCHAR))',
        context: 'VARCHAR',
        outcome_status: 'STRUCT(category VARCHAR, date VARCHAR)',
        persistent_id: 'VARCHAR',
        id: 'BIGINT',
        location_subtype: 'VARCHAR',
        month: 'VARCHAR'
    }
)
