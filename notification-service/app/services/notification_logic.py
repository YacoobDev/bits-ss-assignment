import time
import uuid
import logging
import random
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import NotificationLog
from app.schemas import SendNotificationRequest
from app.config import settings

logger = logging.getLogger(__name__)

def dispatch_notification(db: Session, req: SendNotificationRequest) -> NotificationLog:
    """
    BR-NOTIF-01: Dispatches confirmation notifications (SMS/Email).
    BR-NOTIF-02 & Condition E: Simulates slow delivery and intermittent downstream failures.
    """
    logger.info(f"Sending {req.channel} notification to {req.recipient} for booking ID {req.booking_id}")

    # 1. Simulate Artificial Latency (Condition E)
    if settings.MOCK_SIMULATE_SLOW_SMS > 0 and req.channel.upper() == "SMS":
        logger.info(f"Simulating slow SMS gateway delay of {settings.MOCK_SIMULATE_SLOW_SMS}s")
        time.sleep(settings.MOCK_SIMULATE_SLOW_SMS)

    # 2. Simulate Downstream Provider Failures (Condition E)
    if settings.MOCK_SIMULATE_EMAIL_FAILURE > 0 and random.random() < settings.MOCK_SIMULATE_EMAIL_FAILURE:
        logger.error(f"Simulated notification provider failure for channel {req.channel}")
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "NOTIFICATION_PROVIDER_UNAVAILABLE",
                "message": "Transient failure sending notification via third-party provider."
            }
        )

    notification_id = f"NOTIF_{uuid.uuid4().hex[:10].upper()}"
    log_entry = NotificationLog(
        notification_id=notification_id,
        booking_id=req.booking_id,
        user_id=req.user_id,
        channel=req.channel.upper(),
        recipient=req.recipient,
        message=req.message,
        status="SENT",
        created_at=datetime.utcnow()
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    logger.info(f"Notification successfully delivered with ID {notification_id}")
    return log_entry
