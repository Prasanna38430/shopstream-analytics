"""Centralized Snowflake connection config.

Reads credentials from environment variables (loaded from .env) so that
secrets never appear in source code. Every script that talks to Snowflake
imports get_snowflake_config() from here.
"""
import os
from dotenv import load_dotenv

# Load variables from the .env file in the project root into the environment.
load_dotenv()


def get_snowflake_config() -> dict:
    """Return Snowflake connection parameters as a dict.

    Raises a clear error if any required variable is missing, so we fail
    fast with a helpful message instead of a cryptic connector error.
    """
    config = {
        "account":   os.environ.get("SNOWFLAKE_ACCOUNT"),
        "user":      os.environ.get("SNOWFLAKE_USER"),
        "password":  os.environ.get("SNOWFLAKE_PASSWORD"),
        "role":      os.environ.get("SNOWFLAKE_ROLE"),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE"),
        "database":  os.environ.get("SNOWFLAKE_DATABASE"),
        "schema":    os.environ.get("SNOWFLAKE_SCHEMA"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise EnvironmentError(
            f"Missing Snowflake env vars: {', '.join(missing)}. "
            f"Did you copy .env.example to .env and fill it in?"
        )

    return config


# Quick manual test:  python ingestion/config.py
if __name__ == "__main__":
    cfg = get_snowflake_config()
    safe = {k: (v if k != "password" else "***") for k, v in cfg.items()}
    print("Loaded Snowflake config:", safe)
