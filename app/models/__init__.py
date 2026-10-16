"""Import all models so Base.metadata contains the complete schema."""

from app.models.driver_model import Driver
from app.models.passenger_model import Passenger
from app.models.receipt_model import Receipt
from app.models.trip_model import PaymentStatus, Trip, TripStatus

__all__ = [
    "Driver",
    "Passenger",
    "PaymentStatus",
    "Receipt",
    "Trip",
    "TripStatus",
]
