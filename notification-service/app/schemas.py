from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SendNotificationRequest(BaseModel):
    booking_id: int = Field(..., example=1)
    user_id: str = Field(..., example="usr_123")
    channel: str = Field(..., example="EMAIL")  # EMAIL or SMS
    recipient: str = Field(..., example="user@example.com")
    message: str = Field(..., example="Your turf booking #1 is confirmed!")

class NotificationResponse(BaseModel):
    notification_id: str
    booking_id: int
    user_id: str
    channel: str
    recipient: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
