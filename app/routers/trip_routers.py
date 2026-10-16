"""Start and finish trips, and expose their current state for polling."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import DbSession
from app.models import Driver, Passenger, Receipt, Trip, TripStatus
from app.schemas.trip_schemas import TripCreate, TripFinish, TripRead

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def start_trip(payload: TripCreate, db: DbSession) -> TripRead:
    with db.begin():
        if db.get(Passenger, payload.passenger_id) is None:
            raise HTTPException(status_code=404, detail="Passenger not found.")
        if db.get(Driver, payload.driver_id) is None:
            raise HTTPException(status_code=404, detail="Driver not found.")

        trip = Trip(**payload.model_dump())
        db.add(trip)
        db.flush()
        result = TripRead.model_validate(trip)
    return result


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(trip_id: UUID, db: DbSession) -> TripRead:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found.")
    return TripRead.model_validate(trip)


@router.post("/{trip_id}/finish", response_model=TripRead)
def finish_trip(trip_id: UUID, payload: TripFinish, db: DbSession) -> TripRead:
    with db.begin():
        # Lock the trip so simultaneous finish requests cannot create two receipts.
        trip = db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
        if trip is None:
            raise HTTPException(status_code=404, detail="Trip not found.")

        if trip.status != TripStatus.COMPLETED:
            trip.dropoff_latitude = payload.dropoff_latitude
            trip.dropoff_longitude = payload.dropoff_longitude
            trip.distance_meters = payload.distance_meters
            trip.cost = payload.cost
            trip.currency = payload.currency
            trip.completed_at = datetime.now(timezone.utc)
            trip.status = TripStatus.COMPLETED
            trip.receipt = Receipt(receipt_number=f"TAXI-{trip.id.hex.upper()}")
            db.flush()

        # Repeated finish requests return the original values and receipt.
        result = TripRead.model_validate(trip)
    return result
