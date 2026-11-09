with totals as (
    select
        (select count(*)
         from {{ ref('fct_bicycle_thefts') }}) as fact_total,

        (select sum(total_thefts)
         from {{ ref('mart_monthly_thefts') }}) as monthly_total,

        (select sum(total_thefts)
         from {{ ref('mart_theft_hotspots') }}) as hotspot_total
)

select *
from totals
where fact_total != monthly_total
   or fact_total != hotspot_total
   or monthly_total is null
   or hotspot_total is null
