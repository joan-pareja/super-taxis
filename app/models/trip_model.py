"""Journey details, final price and a single simulated payment state."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.driver_model import Driver
    from app.models.passenger_model import Passenger
    from app.models.receipt_model import Receipt


class TripStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class PaymentStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("length(trim(city)) > 0", name="city_not_blank"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_format"),
        CheckConstraint(
            "(cost IS NULL) = (currency IS NULL)", name="cost_currency_pair"
        ),
        CheckConstraint(
            "pickup_latitude BETWEEN -90 AND 90", name="pickup_latitude_range"
        ),
        CheckConstraint(
            "pickup_longitude BETWEEN -180 AND 180", name="pickup_longitude_range"
        ),
        CheckConstraint(
            "dropoff_latitude BETWEEN -90 AND 90", name="dropoff_latitude_range"
        ),
        CheckConstraint(
            "dropoff_longitude BETWEEN -180 AND 180", name="dropoff_longitude_range"
        ),
        CheckConstraint(
            "(dropoff_latitude IS NULL) = (dropoff_longitude IS NULL)",
            name="dropoff_coordinate_pair",
        ),
        CheckConstraint("distance_meters >= 0", name="distance_nonnegative"),
        CheckConstraint("cost BETWEEN 0 AND 9999999999.99", name="cost_range"),
        CheckConstraint("completed_at >= started_at", name="completion_time_order"),
        CheckConstraint(
            "(status = 'IN_PROGRESS' AND completed_at IS NULL) OR "
            "(status = 'COMPLETED' AND completed_at IS NOT NULL AND "
            "dropoff_latitude IS NOT NULL AND dropoff_longitude IS NOT NULL AND "
            "distance_meters IS NOT NULL AND cost IS NOT NULL AND currency IS NOT NULL)",
            name="completion_details",
        ),
        CheckConstraint(
            "payment_status != 'PAID' OR status = 'COMPLETED'",
            name="payment_requires_completion",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    passenger_id: Mapped[UUID] = mapped_column(
        ForeignKey("passengers.id", ondelete="RESTRICT"), index=True
    )
    driver_id: Mapped[UUID] = mapped_column(
        ForeignKey("drivers.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, native_enum=False, create_constraint=True, name="status"),
        default=TripStatus.IN_PROGRESS,
        server_default=text("'IN_PROGRESS'"),
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            native_enum=False,
            create_constraint=True,
            name="payment_status",
        ),
        default=PaymentStatus.PENDING_PAYMENT,
        server_default=text("'PENDING_PAYMENT'"),
    )
    city: Mapped[str] = mapped_column(String(200))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_latitude: Mapped[float]
    pickup_longitude: Mapped[float]
    dropoff_latitude: Mapped[float | None]
    dropoff_longitude: Mapped[float | None]
    distance_meters: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(3))

    passenger: Mapped[Passenger] = relationship(back_populates="trips")
    driver: Mapped[Driver] = relationship(back_populates="trips")
    # passive_deletes="all" stops SQLAlchemy from clearing the receipt's trip_id.
    # PostgreSQL then blocks deleting a trip that has a receipt.
    receipt: Mapped[Receipt | None] = relationship(
        back_populates="trip",
        passive_deletes="all",
    )
