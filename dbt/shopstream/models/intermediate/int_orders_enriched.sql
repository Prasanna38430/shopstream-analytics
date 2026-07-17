-- One row per order, joined out to customer and product attributes.
-- Inner joins on purpose: every row here has valid dimension keys, so any
-- order pointing at a customer that was removed during email dedup drops
-- out. That keeps the fact table referentially clean.

with orders as (

    select * from {{ ref('stg_orders') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

),

products as (

    select * from {{ ref('stg_products') }}

),

joined as (

    select
        o.order_id,
        o.customer_id,
        o.product_id,
        o.amount,
        o.order_status,
        o.ordered_at,
        o.order_date,

        c.customer_name,
        c.email,
        c.country_code,
        c.signup_date,

        p.product_name,
        p.category,
        p.brand,
        p.price
    from orders o
    inner join customers c on o.customer_id = c.customer_id
    inner join products p on o.product_id = p.product_id

)

select * from joined
