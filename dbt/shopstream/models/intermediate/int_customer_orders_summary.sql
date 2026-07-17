-- Per-customer order behaviour: lifetime value, how often they order, and
-- the first/last time they did. Feeds the customer dimension.

with enriched as (

    select * from {{ ref('int_orders_enriched') }}

),

summary as (

    select
        customer_id,
        count(*)               as order_count,
        round(sum(amount), 2)  as lifetime_value,
        round(avg(amount), 2)  as avg_order_value,
        min(order_date)        as first_order_date,
        max(order_date)        as last_order_date
    from enriched
    group by customer_id

)

select * from summary
