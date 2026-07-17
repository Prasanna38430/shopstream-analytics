with source as (

    select * from {{ source('raw', 'raw_products') }}

),

final as (

    select
        product_id,
        {{ clean_string('name') }}       as product_name,
        -- Categories arrive in mixed case with stray spaces; normalise them.
        initcap(trim(category))          as category,
        -- Missing prices fall back to the overall average so downstream
        -- revenue maths doesn't break on a NULL.
        round(coalesce(price, avg(price) over ()), 2) as price,
        {{ clean_string('brand') }}      as brand
    from source

)

select * from final
