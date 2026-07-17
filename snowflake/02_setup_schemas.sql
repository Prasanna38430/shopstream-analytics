-- ============================================================
--  ShopStream — Schema layers (Medallion architecture)
-- ============================================================

USE ROLE SHOPSTREAM_ROLE;
USE DATABASE SHOPSTREAM;

-- RAW: landing zone. Data loaded exactly as it arrives, untouched.
CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Bronze layer — raw ingested data, no transformations';

-- STAGING: cleaned & standardized by dbt (types cast, nulls handled).
CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'Silver layer — cleaned, typed, deduplicated by dbt';

-- MARTS: business-ready facts & dimensions for analytics/BI.
CREATE SCHEMA IF NOT EXISTS MARTS
    COMMENT = 'Gold layer — star schema facts & dimensions for BI';

-- Confirm they exist.
SHOW SCHEMAS IN DATABASE SHOPSTREAM;
