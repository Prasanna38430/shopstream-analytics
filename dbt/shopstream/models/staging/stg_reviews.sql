with source as (

    select * from {{ source('raw', 'raw_reviews') }}

),

final as (

    select
        review_id,
        product_id,
        customer_id,
        rating,
        {{ clean_string('review_text') }} as review_text,
        created_at                        as reviewed_at
    from source
    where rating between 1 and 5

)

select * from final
