-- ============================================================
--  ShopStream — RAW landing tables
--  Bronze layer: data lands here exactly as generated, warts and
--  all. No constraints, no cleaning — that's dbt's job downstream.
-- ============================================================

USE ROLE SHOPSTREAM_ROLE;
USE DATABASE SHOPSTREAM;
USE SCHEMA RAW;

CREATE OR REPLACE TABLE raw_customers (
    customer_id   NUMBER,
    name          STRING,
    email         STRING,
    country       STRING,
    signup_date   DATE
);

CREATE OR REPLACE TABLE raw_products (
    product_id    NUMBER,
    name          STRING,
    category      STRING,
    price         FLOAT,
    brand         STRING
);

CREATE OR REPLACE TABLE raw_orders (
    order_id      NUMBER,
    customer_id   NUMBER,
    product_id    NUMBER,
    amount        FLOAT,
    status        STRING,
    created_at    TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE raw_reviews (
    review_id     NUMBER,
    product_id    NUMBER,
    customer_id   NUMBER,
    rating        NUMBER,
    review_text   STRING,
    created_at    TIMESTAMP_NTZ
);

-- Sentiment scores written by the ML step (ingestion/score_reviews.py),
-- not loaded from a CSV. Defined here so the table exists before dbt reads it.
CREATE OR REPLACE TABLE review_sentiment (
    review_id        NUMBER,
    sentiment_label  STRING,
    sentiment_score  FLOAT
);
