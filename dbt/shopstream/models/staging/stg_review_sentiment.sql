with source as (

    select * from {{ source('raw', 'review_sentiment') }}

),

final as (

    select
        review_id,
        upper(sentiment_label) as sentiment_label,
        sentiment_score
    from source

)

select * from final
