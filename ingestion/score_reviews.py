"""Score product reviews with a pretrained sentiment model.

Reads raw_reviews from Snowflake, runs each review through DistilBERT, and
writes review_id, a label, and a signed score (-1 to 1) into review_sentiment.

This runs in the isolated ML environment (requirements-ml.txt) because PyTorch
is heavy and only needed here. It stays out of the dbt/ingestion env, out of
CI, and out of the Airflow image; everything downstream just reads the table.

    python ingestion/score_reviews.py
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas
from transformers import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("score_reviews")

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

# The model is binary (positive/negative). When it isn't confident, the review
# is really neutral, so scores within this band of zero get labelled NEUTRAL.
NEUTRAL_BAND = 0.6


def connect():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema="RAW",
    )


def classify(texts: list[str], model) -> tuple[list[str], list[float]]:
    """Turn the model's positive/negative output into a signed score and label."""
    predictions = model(texts, truncation=True, batch_size=32)
    labels, scores = [], []
    for pred in predictions:
        signed = pred["score"] if pred["label"] == "POSITIVE" else -pred["score"]
        if abs(signed) < NEUTRAL_BAND:
            label = "NEUTRAL"
        else:
            label = "POSITIVE" if signed > 0 else "NEGATIVE"
        labels.append(label)
        scores.append(round(signed, 4))
    return labels, scores


def main() -> None:
    con = connect()
    cur = con.cursor()

    cur.execute("select review_id, review_text from raw.raw_reviews order by review_id")
    reviews = pd.DataFrame(cur.fetchall(), columns=["REVIEW_ID", "REVIEW_TEXT"])
    log.info("scoring %s reviews", f"{len(reviews):,}")

    log.info("loading sentiment model")
    model = pipeline("sentiment-analysis")

    labels, scores = classify(reviews["REVIEW_TEXT"].tolist(), model)
    result = pd.DataFrame(
        {
            "REVIEW_ID": reviews["REVIEW_ID"],
            "SENTIMENT_LABEL": labels,
            "SENTIMENT_SCORE": scores,
        }
    )

    cur.execute("truncate table if exists raw.review_sentiment")
    write_pandas(
        con,
        result,
        "REVIEW_SENTIMENT",
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema="RAW",
    )
    log.info("wrote %s sentiment rows to review_sentiment", f"{len(result):,}")
    log.info("label breakdown:\n%s", result["SENTIMENT_LABEL"].value_counts().to_string())

    con.close()


if __name__ == "__main__":
    main()
