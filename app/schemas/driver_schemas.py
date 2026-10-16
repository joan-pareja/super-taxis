"""Driver information available to the demo interface."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    vehicle_registration: str
