"""Payloads for starting, finishing and reading trips."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field

from app.models.trip_model import PaymentStatus, TripStatus


class TripCreate(BaseModel):
    """The backend assigns the trip ID, start time and initial status."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    passenger_id: UUID
    driver_id: UUID
    city: str = Field(min_length=1, max_length=200)
    pickup_latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    pickup_longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class TripFinish(BaseModel):
    """Final journey details; the backend sets the completion time."""

    model_config = ConfigDict(extra="forbid")

    dropoff_latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    dropoff_longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    distance_meters: int = Field(ge=0, le=2147483647, strict=True)
    # Send money as a decimal string, for example "12.50", to preserve precision.
    cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$", min_length=3, max_length=3)


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    passenger_id: UUID
    driver_id: UUID
    status: TripStatus
    payment_status: PaymentStatus
    city: str
    started_at: datetime
    completed_at: datetime | None
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float | None
    dropoff_longitude: float | None
    distance_meters: int | None
    cost: Decimal | None
    currency: str | None
    # Read the ID through the ORM relationship without nesting the whole receipt.
    receipt_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("receipt_id", AliasPath("receipt", "id")),
    )
