"""Receipt details, including the price stored on its trip."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    receipt_number: str
    issued_at: datetime
    # Read these values from the related trip; the receipt table does not copy them.
    cost: Decimal = Field(
        validation_alias=AliasChoices("cost", AliasPath("trip", "cost"))
    )
    currency: str = Field(
        validation_alias=AliasChoices("currency", AliasPath("trip", "currency"))
    )
