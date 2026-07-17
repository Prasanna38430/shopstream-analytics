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
