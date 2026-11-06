-- Staging: typed, trimmed, consistently named, de-duplicated.
-- Tiles overlap, so the same crime can appear in several files. `id` is the
-- crime's identifier in this dataset; persistent_id is often blank, so it is
-- NOT used as the key. We keep one row per id (latest file name wins, so the
-- choice is deterministic and re-runs give identical output).
create or replace table stg_crimes as
select
    id                                              as crime_id,
    nullif(trim(persistent_id), '')                 as persistent_id,
    cast(month || '-01' as date)                    as crime_month,
    lower(trim(category))                           as category,
    nullif(trim(location_type), '')                 as location_type,
    cast(latitude as double)                        as latitude,
    cast(longitude as double)                       as longitude,
    street_id,
    nullif(trim(street_name), '')                   as street_name,
    nullif(trim(context), '')                       as context,
    nullif(trim(outcome_category), '')              as outcome_category,
    try_cast(outcome_date || '-01' as date)         as outcome_month,
    source_month_dir
from raw_crimes
qualify row_number() over (partition by id order by source_file desc) = 1;
