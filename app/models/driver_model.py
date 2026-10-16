"""Driver alias, vehicle registration and trip history."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.trip_model import Trip


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name_not_blank"),
        CheckConstraint(
            "length(trim(vehicle_registration)) > 0",
            name="vehicle_registration_not_blank",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(64))
    vehicle_registration: Mapped[str] = mapped_column(String(32))

    # passive_deletes="all" stops SQLAlchemy from clearing the trips' driver_id.
    # PostgreSQL then blocks deleting a driver who still has trips.
    trips: Mapped[list[Trip]] = relationship(
        back_populates="driver",
        passive_deletes="all",
    )
