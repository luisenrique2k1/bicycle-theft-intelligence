-- Data-quality checks. Each row: check name, number of offending rows. Pipeline fails if any > 0.
select 'crime_id_not_null'      as check_name, count(*) as failures from stg_crimes where crime_id is null
union all
select 'crime_id_unique',        count(*) from (select crime_id from stg_crimes group by crime_id having count(*) > 1)
union all
select 'category_is_bicycle_theft', count(*) from stg_crimes where category <> 'bicycle-theft'
union all
select 'coordinates_inside_uk',  count(*) from stg_crimes
    where latitude not between 49.8 and 60.9 or longitude not between -8.7 and 1.8 or latitude is null or longitude is null
union all
select 'month_matches_folder',   count(*) from stg_crimes
    where strftime(crime_month, '%Y-%m') <> source_month_dir
union all
select 'fact_rows_equal_distinct_raw_ids', abs((select count(*) from fct_bike_theft) - (select count(distinct id) from raw_crimes))
union all
select 'every_fact_street_in_dim', count(*) from fct_bike_theft f
    left join dim_street s using (street_id) where f.street_id is not null and s.street_id is null
union all
select 'street_id_has_one_name', count(*) from (
    select street_id from stg_crimes where street_name is not null group by street_id having count(distinct street_name) > 1)
union all
select 'outcome_not_before_crime', count(*) from stg_crimes where outcome_month is not null and outcome_month < crime_month;
