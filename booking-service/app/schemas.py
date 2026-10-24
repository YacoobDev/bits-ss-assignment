from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional

class HoldSlotRequest(BaseModel):
    user_id: str = Field(..., example="user_123")
    turf_id: int = Field(..., example=1)
    booking_date: date = Field(..., example="2026-10-25")
    start_time: time = Field(..., example="18:00:00")
    end_time: time = Field(..., example="19:00:00")
    amount: float = Field(..., example=1200.0)

class BookingResponse(BaseModel):
    id: int
    user_id: str
    turf_id: int
    booking_date: date
    start_time: time
    end_time: time
    amount: float
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConfirmBookingRequest(BaseModel):
    payment_reference: str = Field(..., example="PAY_89712398")

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
