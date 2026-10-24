from pydantic import BaseModel, Field
from datetime import time, date
from typing import List, Optional

# Venue Schemas
class VenueBase(BaseModel):
    name: str = Field(..., example="Green Field Sports Arena")
    address: str = Field(..., example="123 Main St, Sector 4")
    city: str = Field(..., example="Bangalore")
    opening_time: time = Field(..., example="06:00:00")
    closing_time: time = Field(..., example="23:00:00")

class VenueCreate(VenueBase):
    pass

class VenueResponse(VenueBase):
    id: int

    class Config:
        from_attributes = True


# Turf Schemas
class TurfBase(BaseModel):
    name: str = Field(..., example="Turf A - Football")
    sport_type: str = Field(..., example="Football")
    hourly_rate: float = Field(..., example=1200.0)

class TurfCreate(TurfBase):
    venue_id: int

class TurfResponse(TurfBase):
    id: int
    venue_id: int
    is_active: bool

    class Config:
        from_attributes = True
        
# Slot Schemas
class SlotAvailabilityRequest(BaseModel):
    turf_id: int
    booking_date: date

class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    price: float
    is_available: bool

class SlotAvailabilityResponse(BaseModel):
    turf_id: int
    booking_date: date
    slots: List[TimeSlot]


# Standard Error Format
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None