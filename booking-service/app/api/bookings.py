from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.database import get_db
from app.models import Booking
from app.schemas import HoldSlotRequest, BookingResponse, ConfirmBookingRequest

router = APIRouter(prefix="/api/v1", tags=["Bookings"])

@router.post("/bookings/hold", response_model=BookingResponse, status_code=201)
def hold_slot(req: HoldSlotRequest, db: Session = Depends(get_db)):
    """
    Holds a slot. Safely purges any EXPIRED, CANCELLED, or timed-out bookings 
    for this slot first, allowing infinite reruns of the concurrency stress test.
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=30)

    try:
        # 1. Check if an active (PENDING and not expired, or CONFIRMED) booking exists
        active_booking = db.query(Booking).filter(
            Booking.turf_id == req.turf_id,
            Booking.booking_date == req.booking_date,
            Booking.start_time == req.start_time,
            Booking.status.in_(["CONFIRMED"]) | 
            ((Booking.status == "PENDING") & (Booking.expires_at > now))
        ).first()

        if active_booking:
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "SLOT_ALREADY_BOOKED",
                    "message": "The selected slot is currently held or already confirmed by another user."
                }
            )

        # 2. Purge any stale, EXPIRED, CANCELLED, or past-due PENDING bookings for this slot
        db.query(Booking).filter(
            Booking.turf_id == req.turf_id,
            Booking.booking_date == req.booking_date,
            Booking.start_time == req.start_time,
            Booking.status.in_(["EXPIRED", "CANCELLED"]) | 
            ((Booking.status == "PENDING") & (Booking.expires_at <= now))
        ).delete(synchronize_session=False)
        
        db.flush()

        # 3. Attempt to insert the new booking atomically
        new_booking = Booking(
            user_id=req.user_id,
            turf_id=req.turf_id,
            booking_date=req.booking_date,
            start_time=req.start_time,
            end_time=req.end_time,
            amount=req.amount,
            status="PENDING",
            expires_at=expires_at
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return new_booking

    except HTTPException as he:
        db.rollback()
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "SLOT_ALREADY_BOOKED",
                "message": "The selected slot is currently held or already confirmed by another user."
            }
        )

@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking(booking_id: int, req: ConfirmBookingRequest, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail={"error_code": "BOOKING_NOT_FOUND", "message": "Booking not found."})
    booking.status = "CONFIRMED"
    db.commit()
    db.refresh(booking)
    return booking

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail={"error_code": "BOOKING_NOT_FOUND", "message": "Booking not found."})
    return booking

@router.get("/bookings", response_model=List[BookingResponse])
def list_user_bookings(user_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Booking)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    return query.all()