"""A small Streamlit dashboard over the ShopStream marts.

Reads the gold-layer tables directly (agg_daily_revenue, fact_orders,
dim_customers, product_sentiment) so the pipeline ends in something you can
actually look at rather than just tables in a warehouse.

    streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import snowflake.connector
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from config import get_snowflake_config  # noqa: E402

st.set_page_config(page_title="ShopStream Analytics", layout="wide")


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(**get_snowflake_config())


@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    cur = get_connection().cursor()
    cur.execute(sql)
    return pd.DataFrame(cur.fetchall(), columns=[c[0].lower() for c in cur.description])


st.title("ShopStream Analytics")
st.caption("Gold-layer marts built with dbt on Snowflake, orchestrated by Airflow.")

# --- headline numbers -------------------------------------------------------
kpis = run_query(
    """
    select
        (select round(sum(total_revenue)) from marts.agg_daily_revenue)   as revenue,
        (select sum(order_count) from marts.agg_daily_revenue)            as orders,
        (select count(*) from marts.dim_customers)                        as customers,
        (select round(avg(avg_sentiment_score), 2) from marts.product_sentiment) as sentiment
    """
).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${int(kpis['revenue']):,}")
c2.metric("Orders", f"{int(kpis['orders']):,}")
c3.metric("Customers", f"{int(kpis['customers']):,}")
c4.metric("Avg review sentiment", f"{float(kpis['sentiment']):+.2f}")

# --- revenue over time ------------------------------------------------------
st.subheader("Daily revenue")
daily = run_query(
    "select order_date, total_revenue from marts.agg_daily_revenue order by order_date"
)
st.line_chart(daily.set_index("order_date")["total_revenue"], height=260)

# --- breakdowns -------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Revenue by country")
    by_country = run_query(
        """
        select c.country_code, round(sum(f.amount)) as revenue
        from marts.fact_orders f
        join marts.dim_customers c on f.customer_id = c.customer_id
        where c.country_code is not null
        group by c.country_code
        order by revenue desc
        """
    )
    st.bar_chart(by_country.set_index("country_code")["revenue"], height=280)

with right:
    st.subheader("Sentiment by department")
    by_dept = run_query(
        """
        select department, round(avg(avg_sentiment_score), 3) as sentiment
        from marts.product_sentiment
        where department is not null
        group by department
        order by sentiment desc
        """
    )
    st.bar_chart(by_dept.set_index("department")["sentiment"], height=280)

# --- review sentiment -------------------------------------------------------
st.subheader("Products customers talk about")
best, worst = st.columns(2)

sentiment_cols = ["product_name", "category", "review_count", "avg_rating", "avg_sentiment_score"]

with best:
    st.caption("Best reviewed")
    st.dataframe(
        run_query(
            """
            select product_name, category, review_count, avg_rating, avg_sentiment_score
            from marts.product_sentiment
            where review_count >= 5
            order by avg_sentiment_score desc, review_count desc
            limit 8
            """
        )[sentiment_cols],
        hide_index=True,
        use_container_width=True,
    )

with worst:
    st.caption("Worst reviewed")
    st.dataframe(
        run_query(
            """
            select product_name, category, review_count, avg_rating, avg_sentiment_score
            from marts.product_sentiment
            where review_count >= 5
            order by avg_sentiment_score asc, review_count desc
            limit 8
            """
        )[sentiment_cols],
        hide_index=True,
        use_container_width=True,
    )
