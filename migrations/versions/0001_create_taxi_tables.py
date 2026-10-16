"""Create the initial taxi database tables.

Revision ID: 0001
Revises: None (initial migration)

Summary:
- Creates the drivers, passengers, trips and receipts tables.
- Adds foreign keys, unique receipt identifiers and trip lookup indexes.
- Adds checks for names, coordinates, prices and trip/payment states.

Destructive changes (upgrade):
- None.

Downgrade limitations:
- Drops all four application tables and permanently removes their data.
- Later migrations must be rolled back before this initial migration.

Preview before applying:
    uv run alembic upgrade head --sql
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drivers",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("vehicle_registration", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name=op.f("ck_drivers_name_not_blank")
        ),
        sa.CheckConstraint(
            "length(trim(vehicle_registration)) > 0",
            name=op.f("ck_drivers_vehicle_registration_not_blank"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drivers")),
    )
    op.create_table(
        "passengers",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name=op.f("ck_passengers_name_not_blank")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_passengers")),
    )
    op.create_table(
        "trips",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("passenger_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "IN_PROGRESS",
                "COMPLETED",
                name="status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default=sa.text("'IN_PROGRESS'"),
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "PENDING_PAYMENT",
                "PAID",
                name="payment_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default=sa.text("'PENDING_PAYMENT'"),
            nullable=False,
        ),
        sa.Column("city", sa.String(length=200), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pickup_latitude", sa.Double(), nullable=False),
        sa.Column("pickup_longitude", sa.Double(), nullable=False),
        sa.Column("dropoff_latitude", sa.Double(), nullable=True),
        sa.Column("dropoff_longitude", sa.Double(), nullable=True),
        sa.Column("distance_meters", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.CheckConstraint(
            "(status = 'IN_PROGRESS' AND completed_at IS NULL) OR (status = 'COMPLETED' AND completed_at IS NOT NULL AND dropoff_latitude IS NOT NULL AND dropoff_longitude IS NOT NULL AND distance_meters IS NOT NULL AND cost IS NOT NULL AND currency IS NOT NULL)",
            name=op.f("ck_trips_completion_details"),
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'", name=op.f("ck_trips_currency_format")
        ),
        sa.CheckConstraint(
            "(cost IS NULL) = (currency IS NULL)",
            name=op.f("ck_trips_cost_currency_pair"),
        ),
        sa.CheckConstraint(
            "payment_status != 'PAID' OR status = 'COMPLETED'",
            name=op.f("ck_trips_payment_requires_completion"),
        ),
        sa.CheckConstraint(
            "(dropoff_latitude IS NULL) = (dropoff_longitude IS NULL)",
            name=op.f("ck_trips_dropoff_coordinate_pair"),
        ),
        sa.CheckConstraint(
            "completed_at >= started_at", name=op.f("ck_trips_completion_time_order")
        ),
        sa.CheckConstraint(
            "distance_meters >= 0", name=op.f("ck_trips_distance_nonnegative")
        ),
        sa.CheckConstraint(
            "dropoff_latitude BETWEEN -90 AND 90",
            name=op.f("ck_trips_dropoff_latitude_range"),
        ),
        sa.CheckConstraint(
            "dropoff_longitude BETWEEN -180 AND 180",
            name=op.f("ck_trips_dropoff_longitude_range"),
        ),
        sa.CheckConstraint(
            "cost BETWEEN 0 AND 9999999999.99",
            name=op.f("ck_trips_cost_range"),
        ),
        sa.CheckConstraint(
            "length(trim(city)) > 0", name=op.f("ck_trips_city_not_blank")
        ),
        sa.CheckConstraint(
            "pickup_latitude BETWEEN -90 AND 90",
            name=op.f("ck_trips_pickup_latitude_range"),
        ),
        sa.CheckConstraint(
            "pickup_longitude BETWEEN -180 AND 180",
            name=op.f("ck_trips_pickup_longitude_range"),
        ),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["drivers.id"],
            name=op.f("fk_trips_driver_id_drivers"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["passenger_id"],
            ["passengers.id"],
            name=op.f("fk_trips_passenger_id_passengers"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trips")),
    )
    op.create_index(op.f("ix_trips_driver_id"), "trips", ["driver_id"], unique=False)
    op.create_index(
        op.f("ix_trips_passenger_id"), "trips", ["passenger_id"], unique=False
    )
    op.create_table(
        "receipts",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("receipt_number", sa.String(length=64), nullable=False),
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(receipt_number)) > 0",
            name=op.f("ck_receipts_receipt_number_not_blank"),
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            name=op.f("fk_receipts_trip_id_trips"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_receipts")),
        sa.UniqueConstraint("receipt_number", name=op.f("uq_receipts_receipt_number")),
        sa.UniqueConstraint("trip_id", name=op.f("uq_receipts_trip_id")),
    )


def downgrade() -> None:
    op.drop_table("receipts")
    op.drop_index(op.f("ix_trips_passenger_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_driver_id"), table_name="trips")
    op.drop_table("trips")
    op.drop_table("passengers")
    op.drop_table("drivers")
