-- Product dimension. Rolls the eight categories up into broader departments
-- so reports can slice at either level (a simple two-level hierarchy).

with products as (

    select * from {{ ref('stg_products') }}

),

final as (

    select
        product_id,
        product_name,
        brand,
        category,
        case
            when category = 'Electronics'              then 'Technology'
            when category = 'Books'                    then 'Media'
            when category in ('Clothing', 'Beauty')    then 'Personal Care'
            when category in ('Home & Kitchen', 'Grocery') then 'Household'
            when category in ('Sports', 'Toys')        then 'Leisure'
            else 'Other'
        end as department,
        price
    from products

)

select * from final
