"""ShopStream end-to-end ELT pipeline.

Runs the whole thing once a day:
    generate raw data -> load into Snowflake -> dbt staging -> dbt marts -> dbt tests

The two Python tasks reuse the ingestion scripts (mounted at /opt/airflow/ingestion);
the dbt steps shell out to the dbt CLI against the project mounted at
/opt/airflow/dbt/shopstream. Snowflake credentials come from the container
environment (see docker-compose.yml), so nothing sensitive lives in here.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

INGESTION_DIR = "/opt/airflow/ingestion"
DBT_DIR = "/opt/airflow/dbt/shopstream"


def generate_raw_data(**_):
    """Regenerate the CSVs. Row counts are overridable via Airflow Variables."""
    import random
    import sys

    sys.path.insert(0, INGESTION_DIR)
    from faker import Faker
    from airflow.models import Variable

    import generate_data as gen

    orders = int(Variable.get("shopstream_order_count", default_var=100_000))
    customers = int(Variable.get("shopstream_customer_count", default_var=10_000))
    products = int(Variable.get("shopstream_product_count", default_var=500))

    random.seed(42)
    Faker.seed(42)

    gen.DATA_DIR.mkdir(exist_ok=True)
    gen.generate_customers(customers)
    gen.generate_products(products)
    gen.generate_orders(orders, customers, products)


def ingest_to_snowflake(**_):
    """Stage the CSVs and COPY INTO the RAW tables."""
    import sys

    sys.path.insert(0, INGESTION_DIR)
    import load_to_snowflake as loader

    loader.main()


default_args = {
    "owner": "prasanna",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    # Flip on and configure SMTP in Airflow to get failure emails.
    "email_on_failure": False,
    "email": ["prasannakumar38430@gmail.com"],
}

with DAG(
    dag_id="shopstream_pipeline",
    description="End-to-end ShopStream ELT: generate, ingest, dbt build, test",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 7, 1),
    catchup=False,
    max_active_runs=1,
    tags=["shopstream", "elt", "dbt", "snowflake"],
) as dag:

    generate = PythonOperator(
        task_id="generate_raw_data",
        python_callable=generate_raw_data,
        execution_timeout=timedelta(minutes=10),
    )

    ingest = PythonOperator(
        task_id="ingest_to_snowflake",
        python_callable=ingest_to_snowflake,
        execution_timeout=timedelta(minutes=10),
    )

    dbt_staging = BashOperator(
        task_id="run_dbt_staging",
        bash_command=f"cd {DBT_DIR} && dbt deps && dbt run --select staging",
        execution_timeout=timedelta(minutes=15),
    )

    dbt_marts = BashOperator(
        task_id="run_dbt_marts",
        bash_command=f"cd {DBT_DIR} && dbt run --select marts",
        execution_timeout=timedelta(minutes=15),
    )

    dbt_tests = BashOperator(
        task_id="run_dbt_tests",
        bash_command=f"cd {DBT_DIR} && dbt test",
        execution_timeout=timedelta(minutes=15),
    )

    # Placeholder for the Great Expectations validation added in phase 7.
    data_quality = EmptyOperator(task_id="data_quality_check")

    generate >> ingest >> dbt_staging >> dbt_marts >> dbt_tests >> data_quality
