"""Generate synthetic ShopStream data as CSV files.

Customers and products are built first so that orders can reference IDs
that actually exist. Some deliberate messiness is baked in — duplicate
emails, missing countries and prices, inconsistent country codes, mixed
category casing, a handful of bad order amounts — so the dbt staging layer
later has something realistic to clean up instead of perfect data.

Usage:
    python ingestion/generate_data.py
    python ingestion/generate_data.py --orders 5000 --customers 500 --products 50
"""
from __future__ import annotations

import argparse
import csv
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("generate_data")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CATEGORIES = ["Electronics", "Home & Kitchen", "Books", "Clothing",
              "Sports", "Toys", "Beauty", "Grocery"]

# Weighted so most orders look "healthy" and a minority are edge cases.
ORDER_STATUSES = ["completed", "completed", "completed", "shipped",
                  "shipped", "pending", "cancelled", "returned"]

# Same countries spelled several ways on purpose. Standardising these is
# one of the jobs of stg_customers in phase 3.
COUNTRY_VARIANTS = ["US", "USA", "United States", "UK", "GB", "United Kingdom",
                    "IN", "India", "DE", "Germany", "FR", "France",
                    "CA", "Canada", "AU", "Australia"]

# Review text pools, chosen by star rating so the sentiment model has real
# opinions to work with rather than random words.
REVIEWS_POSITIVE = [
    "Absolutely love this, it exceeded my expectations.",
    "Great quality and fast shipping, would buy again.",
    "Fantastic product, works exactly as described.",
    "Really happy with this purchase, highly recommend it.",
    "Excellent value for the price, very satisfied.",
    "Better than I hoped, this is genuinely brilliant.",
]
REVIEWS_NEUTRAL = [
    "It works fine, nothing special.",
    "Okay product, does the job but feels a bit cheap.",
    "Average quality, about what I expected for the price.",
    "It is alright, not great but not bad either.",
    "Decent enough, though I have seen better.",
]
REVIEWS_NEGATIVE = [
    "Terrible quality, it broke after one day.",
    "Very disappointed, it does not work as advertised.",
    "Waste of money, I would not recommend it.",
    "Poor build quality and the delivery was slow.",
    "Awful experience, the item arrived damaged.",
]

fake = Faker()


def _messy_category(name: str) -> str:
    """Return the category with occasional casing / whitespace noise."""
    roll = random.random()
    if roll < 0.15:
        return name.upper()
    if roll < 0.30:
        return name.lower()
    if roll < 0.38:
        return f" {name} "          # stray whitespace
    return name


def generate_customers(n: int) -> None:
    path = DATA_DIR / "raw_customers.csv"
    seen_emails: list[str] = []
    start = datetime(2022, 1, 1)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "name", "email", "country", "signup_date"])

        for customer_id in range(1, n + 1):
            name = fake.name()

            # ~1.5% of rows reuse an earlier email -> duplicates to dedup later
            if seen_emails and random.random() < 0.015:
                email = random.choice(seen_emails)
            else:
                email = fake.unique.email()
                seen_emails.append(email)

            # ~2% missing country
            country = "" if random.random() < 0.02 else random.choice(COUNTRY_VARIANTS)

            signup = start + timedelta(days=random.randint(0, 1000))

            writer.writerow([customer_id, name, email, country,
                             signup.strftime("%Y-%m-%d")])

    log.info("wrote %s customers -> %s", f"{n:,}", path.name)


def generate_products(n: int) -> None:
    path = DATA_DIR / "raw_products.csv"

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "name", "category", "price", "brand"])

        for product_id in range(1, n + 1):
            name = fake.catch_phrase()
            category = _messy_category(random.choice(CATEGORIES))
            brand = fake.company()

            # ~3% missing price -> stg_products fills a fallback in phase 3
            price = "" if random.random() < 0.03 else round(random.uniform(5, 500), 2)

            writer.writerow([product_id, name, category, price, brand])

    log.info("wrote %s products -> %s", f"{n:,}", path.name)


def generate_orders(n: int, n_customers: int, n_products: int) -> None:
    path = DATA_DIR / "raw_orders.csv"
    now = datetime.now()

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "customer_id", "product_id",
                         "amount", "status", "created_at"])

        for order_id in range(1, n + 1):
            customer_id = random.randint(1, n_customers)
            product_id = random.randint(1, n_products)
            status = random.choice(ORDER_STATUSES)

            # ~0.3% get a zero or negative amount — bad data that the
            # staging layer should filter and the phase 5 test guards against
            if random.random() < 0.003:
                amount = round(random.uniform(-50, 0), 2)
            else:
                amount = round(random.uniform(5, 2000), 2)

            created = now - timedelta(
                seconds=random.randint(0, 365 * 24 * 60 * 60)
            )

            writer.writerow([order_id, customer_id, product_id, amount, status,
                             created.strftime("%Y-%m-%d %H:%M:%S")])

    log.info("wrote %s orders -> %s", f"{n:,}", path.name)


def generate_reviews(n: int, n_customers: int, n_products: int) -> None:
    path = DATA_DIR / "raw_reviews.csv"
    now = datetime.now()

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["review_id", "product_id", "customer_id",
                         "rating", "review_text", "created_at"])

        for review_id in range(1, n + 1):
            product_id = random.randint(1, n_products)
            customer_id = random.randint(1, n_customers)
            # Ratings skew positive like real reviews do.
            rating = random.choices([5, 4, 3, 2, 1], weights=[40, 30, 15, 8, 7])[0]

            if rating >= 4:
                text = random.choice(REVIEWS_POSITIVE)
            elif rating == 3:
                text = random.choice(REVIEWS_NEUTRAL)
            else:
                text = random.choice(REVIEWS_NEGATIVE)

            created = now - timedelta(seconds=random.randint(0, 365 * 24 * 60 * 60))

            writer.writerow([review_id, product_id, customer_id, rating, text,
                             created.strftime("%Y-%m-%d %H:%M:%S")])

    log.info("wrote %s reviews -> %s", f"{n:,}", path.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ShopStream synthetic data")
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--customers", type=int, default=10_000)
    parser.add_argument("--products", type=int, default=500)
    parser.add_argument("--reviews", type=int, default=3_000)
    parser.add_argument("--seed", type=int, default=42,
                        help="fixed seed so runs are reproducible")
    args = parser.parse_args()

    # Seed both random and Faker so the same seed always yields the same data.
    random.seed(args.seed)
    Faker.seed(args.seed)

    DATA_DIR.mkdir(exist_ok=True)
    log.info("generating data into %s", DATA_DIR)

    generate_customers(args.customers)
    generate_products(args.products)
    generate_orders(args.orders, args.customers, args.products)
    generate_reviews(args.reviews, args.customers, args.products)

    log.info("done")


if __name__ == "__main__":
    main()
