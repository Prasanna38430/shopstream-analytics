{{
    config(
        materialized='incremental',
        unique_key='order_id'
    )
}}

-- Grain: one row per order. Holds the foreign keys out to the customer and
-- product dimensions plus the order's measure (amount) and dates.
--
-- Incremental so daily runs only process new orders instead of rebuilding
-- all ~98k rows every time. unique_key handles any late-arriving updates to
-- an order that already exists.

with enriched as (

    select * from {{ ref('int_orders_enriched') }}

),

final as (

    select
        order_id,
        customer_id,
        product_id,
        order_status,
        amount,
        ordered_at,
        order_date
    from enriched

    {% if is_incremental() %}
    -- Only pull orders newer than the latest one already loaded.
    where ordered_at > (select coalesce(max(ordered_at), '1900-01-01'::timestamp) from {{ this }})
    {% endif %}

)

select * from final
