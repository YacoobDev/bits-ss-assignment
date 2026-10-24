from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import SendNotificationRequest, NotificationResponse
from app.services.notification_logic import dispatch_notification
from app.models import NotificationLog

router = APIRouter(prefix="/api/v1", tags=["Notifications"])

@router.post("/notifications/send", response_model=NotificationResponse, status_code=201)
def send_notification(req: SendNotificationRequest, db: Session = Depends(get_db)):
    """
    Sends an Email or SMS notification for a booking event.
    """
    return dispatch_notification(db, req)

@router.get("/notifications", response_model=List[NotificationResponse])
def list_notifications(booking_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    query = db.query(NotificationLog)
    if booking_id:
        query = query.filter(NotificationLog.booking_id == booking_id)
    return query.all()
