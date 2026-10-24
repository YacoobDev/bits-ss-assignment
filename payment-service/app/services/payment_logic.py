import time
import json
import uuid
import hashlib
import logging
import random
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, Response

from app.models import IdempotencyRecord, PaymentTransaction
from app.schemas import PaymentChargeRequest
from app.config import settings

logger = logging.getLogger(__name__)

def compute_request_hash(payload: dict) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def process_payment_charge(db: Session, idempotency_key: str, req: PaymentChargeRequest) -> Response:
    """
    BR-PAY-01 & Challenge 2: Idempotency enforcement on payment charges.
    BR-PAY-02 & Condition E: Simulated failure rate and artificial latency.
    """
    if not idempotency_key:
        logger.warning("Payment charge attempted without Idempotency-Key header.")
        raise HTTPException(
            status_code=400,
            detail={"error_code": "MISSING_IDEMPOTENCY_KEY", "message": "Idempotency-Key header is mandatory for payment requests."}
        )

    payload_dict = req.dict()
    request_hash = compute_request_hash(payload_dict)

    # 1. Check if Idempotency Key already exists
    existing_record = db.query(IdempotencyRecord).filter(
        IdempotencyRecord.idempotency_key == idempotency_key
    ).first()

    if existing_record:
        logger.info(f"Replay detected for Idempotency Key: {idempotency_key}")
        if existing_record.request_hash != request_hash:
            logger.warning(f"Payload mismatch for key {idempotency_key}. Expected hash {existing_record.request_hash}, got {request_hash}")
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "IDEMPOTENCY_KEY_REUSE_PAYLOAD_MISMATCH",
                    "message": "Idempotency key was previously used with a different request payload."
                }
            )
        
        # Return cached response
        logger.info(f"Returning cached response for idempotency key {idempotency_key}")
        return Response(
            content=existing_record.response_body,
            status_code=existing_record.response_code,
            media_type="application/json"
        )

    # 2. Simulate Latency / Slowness (Condition E / Challenge 3A)
    if settings.MOCK_LATENCY_SECONDS > 0:
        logger.info(f"Simulating network latency of {settings.MOCK_LATENCY_SECONDS}s")
        time.sleep(settings.MOCK_LATENCY_SECONDS)

    # 3. Simulate Random Downstream Failure (Condition E)
    if settings.MOCK_FAILURE_RATE > 0 and random.random() < settings.MOCK_FAILURE_RATE:
        logger.error("Simulated payment gateway transient failure (500 Internal Server Error).")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PAYMENT_GATEWAY_FAILURE", "message": "Simulated downstream payment gateway fault."}
        )

    # 4. Process new charge
    tx_id = f"TXN_{uuid.uuid4().hex[:10].upper()}"
    now_iso = datetime.utcnow().isoformat()
    
    transaction = PaymentTransaction(
        transaction_id=tx_id,
        booking_id=req.booking_id,
        user_id=req.user_id,
        amount=req.amount,
        status="SUCCESS",
        idempotency_key=idempotency_key
    )
    db.add(transaction)

    response_data = {
        "transaction_id": tx_id,
        "booking_id": req.booking_id,
        "user_id": req.user_id,
        "amount": req.amount,
        "status": "SUCCESS",
        "created_at": now_iso
    }
    response_body = json.dumps(response_data)

    # 5. Store Idempotency Record
    idemp_record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_code=201,
        response_body=response_body
    )
    db.add(idemp_record)
    db.commit()

    logger.info(f"Payment processed successfully with TX ID {tx_id} for key {idempotency_key}")
    return Response(content=response_body, status_code=201, media_type="application/json")
