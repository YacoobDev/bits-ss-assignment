import hashlib
import json
from fastapi import Request, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import IdempotencyRecord

def compute_fingerprint(method: str, path: str, body: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(method.encode())
    hasher.update(path.encode())
    hasher.update(body)
    return hasher.hexdigest()

async def check_idempotency(request: Request):
    if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
        return None

    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return None  # Or raise HTTPException if Idempotency-Key is mandatory for all unsafe requests

    body_bytes = await request.body()
    fingerprint = compute_fingerprint(request.method, request.url.path, body_bytes)

    db = SessionLocal()
    try:
        record = db.query(IdempotencyRecord).filter_by(idempotency_key=idempotency_key).first()
        if record:
            if record.request_fingerprint != fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with a different request payload."
                )
            # Return cached response details for short-circuiting in route/middleware
            return {
                "cached": True,
                "status_code": record.response_status_code,
                "body": json.loads(record.response_body)
            }
        return {"cached": False, "key": idempotency_key, "fingerprint": fingerprint}
    finally:
        db.close()