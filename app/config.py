"""Read database settings explicitly from .env."""

from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import URL

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def get_database_url() -> URL:
    """Build the connection URL using only the project's .env file."""
    values = dotenv_values(ENV_FILE, interpolate=False)
    port = values["POSTGRES_PORT"]
    if port is None:
        raise ValueError("POSTGRES_PORT must have a value in .env.")
    return URL.create(
        "postgresql+psycopg",
        username=values["POSTGRES_USER"],
        password=values["POSTGRES_PASSWORD"],
        host=values["POSTGRES_HOST"],
        port=int(port),
        database=values["POSTGRES_DB"],
    )
