-- Dimensional model.
create or replace table dim_month as
select distinct
    crime_month                          as month_start,
    year(crime_month)                    as year,
    month(crime_month)                   as month_number,
    strftime(crime_month, '%B %Y')       as month_label
from stg_crimes;

create or replace table dim_street as
select
    street_id,
    -- a street id should have one name; pick deterministically if data disagrees
    min(street_name)                     as street_name,
    avg(latitude)                        as centre_latitude,
    avg(longitude)                       as centre_longitude
from stg_crimes
where street_id is not null
group by street_id;

create or replace table fct_bike_theft as
select
    crime_id,
    persistent_id,
    crime_month                          as month_start,
    street_id,
    latitude,
    longitude,
    location_type,
    context
from stg_crimes;

create or replace table fct_outcome as
select
    crime_id,
    coalesce(outcome_category, 'No outcome recorded yet') as outcome_category,
    outcome_month
from stg_crimes;
