"""Passenger alias and trip history."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.trip_model import Trip


class Passenger(Base):
    __tablename__ = "passengers"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="name_not_blank"),)

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(64))

    # passive_deletes="all" stops SQLAlchemy from clearing the trips' passenger_id.
    # PostgreSQL then blocks deleting a passenger who still has trips.
    trips: Mapped[list[Trip]] = relationship(
        back_populates="passenger",
        passive_deletes="all",
    )
