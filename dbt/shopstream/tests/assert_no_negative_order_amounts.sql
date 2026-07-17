-- Singular test: fact_orders should never contain a zero or negative amount.
-- Staging already filters these, so this guards against a regression. A test
-- passes when it returns no rows.

select
    order_id,
    amount
from {{ ref('fact_orders') }}
where amount <= 0
