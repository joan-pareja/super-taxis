"""Use the ORM metadata to compare and migrate the database schema."""

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401 - Register every table in Base.metadata.
from app.config import get_database_url
from app.database import Base


def run_migrations_offline() -> None:
    """Generate migration SQL without connecting to PostgreSQL."""
    context.configure(
        url=get_database_url(),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations inside a database transaction."""
    engine = create_engine(get_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
