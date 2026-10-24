from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas import PaymentChargeRequest, PaymentChargeResponse
from app.services.payment_logic import process_payment_charge

router = APIRouter(prefix="/api/v1", tags=["Payments"])

@router.post("/payments/charge", response_model=PaymentChargeResponse, status_code=201)
def charge_payment(
    req: PaymentChargeRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Charges a payment for a booking. Requires 'Idempotency-Key' in headers (Challenge 2).
    """
    return process_payment_charge(db, idempotency_key, req)
