"""List passengers for the demo's passenger selector."""

from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import DbSession
from app.models import Passenger
from app.schemas.passenger_schemas import PassengerRead

router = APIRouter(prefix="/passengers", tags=["Passengers"])


@router.get("", response_model=list[PassengerRead])
def list_passengers(db: DbSession) -> list[Passenger]:
    return list(db.scalars(select(Passenger).order_by(Passenger.name, Passenger.id)))
