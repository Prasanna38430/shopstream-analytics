with source as (

    select * from {{ source('raw', 'raw_orders') }}

),

final as (

    select
        order_id,
        customer_id,
        product_id,
        amount,
        lower(status)              as order_status,
        created_at                 as ordered_at,
        cast(created_at as date)   as order_date
    from source
    -- Zero and negative amounts are junk data; keep them out of everything
    -- downstream. The phase 5 test asserts none slip through.
    where amount > 0

)

select * from final
