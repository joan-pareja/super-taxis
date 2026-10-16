"""Provide one database session per API request."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_database_url

engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    # Closing the session also rolls back any unfinished transaction.
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]
