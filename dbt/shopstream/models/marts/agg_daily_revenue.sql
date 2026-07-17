-- Daily revenue rollup for dashboards - one row per day with the headline
-- numbers. Built on the fact table so it inherits its referential cleanliness.

with orders as (

    select * from {{ ref('fact_orders') }}

),

daily as (

    select
        order_date,
        count(*)                    as order_count,
        count(distinct customer_id) as unique_customers,
        round(sum(amount), 2)       as total_revenue,
        round(avg(amount), 2)       as avg_order_value
    from orders
    group by order_date

)

select * from daily
order by order_date
