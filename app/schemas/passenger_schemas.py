"""Passenger information available to the demo interface."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PassengerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
