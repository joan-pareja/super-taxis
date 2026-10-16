"""List drivers for the demo's driver selector."""

from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import DbSession
from app.models import Driver
from app.schemas.driver_schemas import DriverRead

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverRead])
def list_drivers(db: DbSession) -> list[Driver]:
    return list(db.scalars(select(Driver).order_by(Driver.name, Driver.id)))
