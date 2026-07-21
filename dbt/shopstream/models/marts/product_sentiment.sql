-- Sentiment rolled up to one row per product that has reviews. Combines the
-- star ratings with the model's sentiment scores, alongside the product's
-- name and category from the dimension.

with reviews as (

    select * from {{ ref('stg_reviews') }}

),

sentiment as (

    select * from {{ ref('stg_review_sentiment') }}

),

products as (

    select * from {{ ref('dim_products') }}

),

joined as (

    select
        r.product_id,
        r.rating,
        s.sentiment_label,
        s.sentiment_score
    from reviews r
    inner join sentiment s on r.review_id = s.review_id

),

final as (

    select
        j.product_id,
        p.product_name,
        p.category,
        p.department,
        count(*)                          as review_count,
        round(avg(j.rating), 2)           as avg_rating,
        round(avg(j.sentiment_score), 3)  as avg_sentiment_score,
        round(100.0 * sum(case when j.sentiment_label = 'POSITIVE' then 1 else 0 end)
              / count(*), 1)              as pct_positive
    from joined j
    left join products p on j.product_id = p.product_id
    group by j.product_id, p.product_name, p.category, p.department

)

select * from final
