"""Load the generated CSVs into Snowflake RAW using an internal stage.

The flow for each table is the classic Snowflake bulk-load pattern:
    1. PUT the local CSV onto an internal stage (Snowflake compresses it)
    2. COPY INTO the target table from that stage
    3. count the rows to confirm the load

Run after generate_data.py has produced the CSVs:
    python ingestion/load_to_snowflake.py
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import snowflake.connector

from config import get_snowflake_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("load_to_snowflake")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FILE_FORMAT = "shopstream_csv"
STAGE = "raw_stage"

# target table -> source csv file
TABLES = {
    "raw_customers": "raw_customers.csv",
    "raw_products": "raw_products.csv",
    "raw_orders": "raw_orders.csv",
}


def load_table(cur, table: str, filename: str) -> int:
    """Stage one CSV and COPY it into its table. Returns the row count."""
    # PUT resolves relative paths against the process cwd, so we run from the
    # data directory. This sidesteps the spaces in the absolute project path,
    # which the PUT command parser doesn't handle cleanly.
    put = (
        f"PUT file://{filename} @{STAGE}/{table}/ "
        f"OVERWRITE = TRUE AUTO_COMPRESS = TRUE"
    )
    cur.execute(put)
    log.info("[%s] staged %s", table, filename)

    cur.execute(f"TRUNCATE TABLE IF EXISTS {table}")
    cur.execute(
        f"COPY INTO {table} "
        f"FROM @{STAGE}/{table}/ "
        f"FILE_FORMAT = (FORMAT_NAME = {FILE_FORMAT}) "
        f"ON_ERROR = 'ABORT_STATEMENT'"
    )

    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    log.info("[%s] loaded %s rows", table, f"{count:,}")
    return count


def main() -> None:
    cfg = get_snowflake_config()
    log.info("connecting to Snowflake account %s", cfg["account"])
    con = snowflake.connector.connect(**cfg)

    try:
        cur = con.cursor()
        cur.execute("USE SCHEMA RAW")

        # A reusable CSV format: skip the header row, treat empty fields as
        # NULL, and allow quoted values (names/companies can contain commas).
        cur.execute(
            f"""
            CREATE FILE FORMAT IF NOT EXISTS {FILE_FORMAT}
                TYPE = 'CSV'
                SKIP_HEADER = 1
                FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                NULL_IF = ('', 'NULL')
                EMPTY_FIELD_AS_NULL = TRUE
            """
        )
        cur.execute(f"CREATE STAGE IF NOT EXISTS {STAGE} FILE_FORMAT = {FILE_FORMAT}")

        os.chdir(DATA_DIR)

        total = 0
        for table, filename in TABLES.items():
            total += load_table(cur, table, filename)

        log.info("all tables loaded - %s rows total", f"{total:,}")
    finally:
        con.close()
        log.info("connection closed")


if __name__ == "__main__":
    main()
