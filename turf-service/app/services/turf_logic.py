from datetime import time, datetime, timedelta
from typing import List
from fastapi import HTTPException
from app.schemas import TimeSlot

def validate_operating_hours(opening_time: time, closing_time: time):
    """
    BR-TURF-01: Closing time must be strictly after opening time.
    """
    if closing_time <= opening_time:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_OPERATING_HOURS",
                "message": "Closing time must be strictly after opening time."
            }
        )

def generate_hourly_slots(opening_time: time, closing_time: time, hourly_rate: float) -> List[TimeSlot]:
    """
    BR-TURF-02: Turf slots are fixed 1-hour durations generated between operating hours.
    """
    slots = []
    current_dt = datetime.combine(datetime.today(), opening_time)
    end_dt = datetime.combine(datetime.today(), closing_time)

    while current_dt + timedelta(hours=1) <= end_dt:
        slot_start = current_dt.time()
        slot_end = (current_dt + timedelta(hours=1)).time()
        slots.append(
            TimeSlot(
                start_time=slot_start,
                end_time=slot_end,
                price=hourly_rate,
                is_available=True
            )
        )
        current_dt += timedelta(hours=1)
        
    return slots
