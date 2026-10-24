from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PaymentChargeRequest(BaseModel):
    booking_id: int = Field(..., example=1)
    user_id: str = Field(..., example="usr_123")
    amount: float = Field(..., example=1200.0)

class PaymentChargeResponse(BaseModel):
    transaction_id: str
    booking_id: int
    user_id: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
