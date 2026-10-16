"""Shared metadata for ORM models and future Alembic migrations."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Register every model in one shared description of the database schema.

    SQLAlchemy adds each model's tables, columns, foreign keys, and other
    constraints to metadata. It can use this information to create tables;
    Alembic can compare it with an existing database to generate migrations.

    The naming convention below gives constraints and indexes predictable names,
    making them easier to identify in database errors and refer to in migrations.
    """

    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "ix": "ix_%(table_name)s_%(column_0_name)s",
        }
    )
