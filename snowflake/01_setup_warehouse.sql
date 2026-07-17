-- ============================================================
--  ShopStream — Warehouse, Database & Role setup
--  Run as ACCOUNTADMIN in a Snowflake worksheet.
-- ============================================================

USE ROLE ACCOUNTADMIN;

-- 1. A compute warehouse. XSMALL is the cheapest; auto-suspend
--    after 60s of inactivity so we don't burn trial credits.
CREATE WAREHOUSE IF NOT EXISTS SHOPSTREAM_WH
    WAREHOUSE_SIZE      = 'XSMALL'
    AUTO_SUSPEND        = 60
    AUTO_RESUME         = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT             = 'Compute for ShopStream ELT pipeline';

-- 2. The database that holds all our schemas.
CREATE DATABASE IF NOT EXISTS SHOPSTREAM
    COMMENT = 'ShopStream e-commerce analytics warehouse';

-- 3. A dedicated role for the pipeline (least-privilege principle —
--    we don't run day-to-day work as ACCOUNTADMIN).
CREATE ROLE IF NOT EXISTS SHOPSTREAM_ROLE;

-- 4. Grant that role the privileges it needs.
GRANT USAGE   ON WAREHOUSE SHOPSTREAM_WH TO ROLE SHOPSTREAM_ROLE;
GRANT OPERATE ON WAREHOUSE SHOPSTREAM_WH TO ROLE SHOPSTREAM_ROLE;
GRANT ALL     ON DATABASE  SHOPSTREAM    TO ROLE SHOPSTREAM_ROLE;

-- 5. Give YOUR user the role. Replace with your actual username.
--    (Find it by running:  SELECT CURRENT_USER();  )
GRANT ROLE SHOPSTREAM_ROLE TO USER PRASANNA38430;
