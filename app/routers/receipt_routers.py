"""Read a generated receipt with the cost and currency from its trip."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.dependencies import DbSession
from app.models import Receipt
from app.schemas.receipt_schemas import ReceiptRead

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.get("/{receipt_id}", response_model=ReceiptRead)
def get_receipt(receipt_id: UUID, db: DbSession) -> ReceiptRead:
    receipt = db.scalar(
        select(Receipt)
        # Load the trip in the same query so reading cost and currency needs no extra query.
        .options(joinedload(Receipt.trip))
        .where(Receipt.id == receipt_id)
    )
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found.")
    return ReceiptRead.model_validate(receipt)
