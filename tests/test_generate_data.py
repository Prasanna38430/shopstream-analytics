"""Unit tests for the synthetic data generator.

These run without Snowflake, so they're cheap to run in CI on every push.
Each test points the generator at a temp directory and checks the CSV it
writes.
"""
import csv
import random
import sys
from pathlib import Path

import pytest
from faker import Faker

INGESTION = Path(__file__).resolve().parent.parent / "ingestion"
sys.path.insert(0, str(INGESTION))

import generate_data as gen


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Redirect the generator's output to a temp dir and seed for determinism.

    The generator's Faker instance keeps a global 'unique' tracker, so we clear
    it here to stop one test's emails leaking into the next.
    """
    monkeypatch.setattr(gen, "DATA_DIR", tmp_path)
    random.seed(1)
    Faker.seed(1)
    gen.fake.unique.clear()
    return tmp_path


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_customers_have_expected_shape(data_dir):
    gen.generate_customers(100)
    rows = read_csv(data_dir / "raw_customers.csv")
    header, body = rows[0], rows[1:]

    assert header == ["customer_id", "name", "email", "country", "signup_date"]
    assert len(body) == 100
    # IDs run 1..N in order.
    assert body[0][0] == "1"
    assert body[-1][0] == "100"


def test_products_prices_are_blank_or_positive(data_dir):
    gen.generate_products(50)
    body = read_csv(data_dir / "raw_products.csv")[1:]

    assert len(body) == 50
    for row in body:
        price = row[3]
        if price:  # some are intentionally blank
            assert float(price) > 0


def test_orders_reference_valid_customers_and_products(data_dir):
    gen.generate_orders(200, n_customers=100, n_products=50)
    body = read_csv(data_dir / "raw_orders.csv")[1:]

    assert len(body) == 200
    for row in body:
        customer_id, product_id = int(row[1]), int(row[2])
        assert 1 <= customer_id <= 100
        assert 1 <= product_id <= 50


def test_generation_is_reproducible(data_dir, tmp_path, monkeypatch):
    """Same seed -> identical output, which is what makes runs reproducible."""
    gen.generate_customers(20)
    first = (data_dir / "raw_customers.csv").read_text(encoding="utf-8")

    second_dir = tmp_path / "again"
    second_dir.mkdir()
    monkeypatch.setattr(gen, "DATA_DIR", second_dir)
    random.seed(1)
    Faker.seed(1)
    gen.fake.unique.clear()
    gen.generate_customers(20)
    second = (second_dir / "raw_customers.csv").read_text(encoding="utf-8")

    assert first == second
