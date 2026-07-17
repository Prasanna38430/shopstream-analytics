-- Customer dimension: one row per customer with descriptive attributes and
-- the order-behaviour metrics. Left join keeps customers who've never
-- ordered (they show up with zeroed-out metrics).

with customers as (

    select * from {{ ref('stg_customers') }}

),

summary as (

    select * from {{ ref('int_customer_orders_summary') }}

),

final as (

    select
        c.customer_id,
        c.customer_name,
        c.email,
        c.country_code,
        c.signup_date,

        coalesce(s.order_count, 0)     as order_count,
        coalesce(s.lifetime_value, 0)  as lifetime_value,
        coalesce(s.avg_order_value, 0) as avg_order_value,
        s.first_order_date,
        s.last_order_date
    from customers c
    left join summary s on c.customer_id = s.customer_id

)

select * from final
