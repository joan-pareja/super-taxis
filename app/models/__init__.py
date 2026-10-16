"""Import all models so Base.metadata contains the complete schema."""

from app.models.driver import Driver
from app.models.passenger import Passenger
from app.models.receipt import Receipt
from app.models.trip import PaymentStatus, Trip, TripStatus

__all__ = [
    "Driver",
    "Passenger",
    "PaymentStatus",
    "Receipt",
    "Trip",
    "TripStatus",
]
