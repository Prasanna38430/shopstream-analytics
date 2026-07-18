"""Great Expectations validation for the ShopStream mart tables.

Reads fact_orders and dim_customers straight from Snowflake into pandas and
runs an expectation suite over each. Full results are written to JSON for an
audit trail; the process exits non-zero if any expectation fails, so an
orchestrator (Airflow) can treat it as a quality gate.

Runs in its own environment because GE clashes with dbt:
    source .venv-ge/Scripts/activate
    python great_expectations/validate_marts.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

import great_expectations as gx
import great_expectations.expectations as gxe

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "great_expectations" / "uncommitted" / "validations"

load_dotenv(REPO_ROOT / ".env")

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Note: build each suite from a list in the constructor. GE 1.2's
# add_expectation() dedupes by column and silently drops a second expectation
# on a column that already has one (e.g. not_null + unique on the same key),
# whereas the constructor keeps them all.


def fact_orders_expectations() -> list:
    return [
        gxe.ExpectTableRowCountToBeBetween(min_value=1000),
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToBeUnique(column="order_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="product_id"),
        gxe.ExpectColumnValuesToBeBetween(
            column="amount", min_value=0, max_value=100000, strict_min=True
        ),
        gxe.ExpectColumnValuesToBeInSet(
            column="order_status",
            value_set=["completed", "shipped", "pending", "cancelled", "returned"],
        ),
    ]


def dim_customers_expectations() -> list:
    return [
        gxe.ExpectTableRowCountToBeBetween(min_value=1000),
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gxe.ExpectColumnValuesToBeUnique(column="customer_id"),
        gxe.ExpectColumnValuesToMatchRegex(column="email", regex=EMAIL_REGEX),
        # Some customers legitimately have no country in the source, so we
        # tolerate a small share of nulls rather than demanding 100%.
        gxe.ExpectColumnValuesToNotBeNull(column="country_code", mostly=0.95),
    ]


def fetch_df(conn, table: str) -> pd.DataFrame:
    """Pull a whole mart table into a DataFrame with lower-cased columns."""
    cur = conn.cursor()
    cur.execute(f"select * from marts.{table}")
    columns = [d[0].lower() for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=columns)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
    )

    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas(name="shopstream_marts")

    fact_suite = context.suites.add(
        gx.ExpectationSuite(name="fact_orders_suite", expectations=fact_orders_expectations())
    )
    dim_suite = context.suites.add(
        gx.ExpectationSuite(name="dim_customers_suite", expectations=dim_customers_expectations())
    )

    checks = [
        ("fact_orders", fact_suite),
        ("dim_customers", dim_suite),
    ]

    all_passed = True
    for table, suite in checks:
        df = fetch_df(conn, table)

        asset = source.add_dataframe_asset(name=table)
        batch_definition = asset.add_batch_definition_whole_dataframe(f"{table}_batch")
        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(name=f"{table}_validation", data=batch_definition, suite=suite)
        )
        result = validation_definition.run(batch_parameters={"dataframe": df})

        result_dict = result.to_json_dict()
        out_path = RESULTS_DIR / f"{table}_{stamp}.json"
        out_path.write_text(json.dumps(result_dict, indent=2, default=str))

        stats = result_dict.get("statistics", {})
        passed = result.success
        all_passed = all_passed and passed
        status = "PASS" if passed else "FAIL"
        print(
            f"[{status}] {table}: "
            f"{stats.get('successful_expectations')}/{stats.get('evaluated_expectations')} "
            f"expectations met ({len(df):,} rows) -> {out_path.name}"
        )

    conn.close()

    if not all_passed:
        print("Data quality checks FAILED")
        sys.exit(1)
    print("All data quality checks passed")


if __name__ == "__main__":
    main()
