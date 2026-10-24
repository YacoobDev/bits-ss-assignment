import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models import Booking
from app.schemas import HoldSlotRequest
from app.config import settings

logger = logging.getLogger(__name__)

def hold_booking_slot(db: Session, req: HoldSlotRequest) -> Booking:
    """
    BR-BOOK-01: Time-Bound Slot Reservation (Challenge 3B) & Concurrency Guard (Challenge 1).
    Locks the slot in PENDING status for HOLD_DURATION_SECONDS (30s default).
    Prevents duplicate active locks for the same slot and cleans up expired rows.
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=settings.HOLD_DURATION_SECONDS)

    logger.info(f"Attempting to hold slot for user {req.user_id} on turf {req.turf_id} at {req.booking_date} {req.start_time}")

    existing_booking = db.query(Booking).filter(
        Booking.turf_id == req.turf_id,
        Booking.booking_date == req.booking_date,
        Booking.start_time == req.start_time
    ).first()

    if existing_booking:
        logger.info(f"Found existing booking record {existing_booking.id} with status {existing_booking.status} for this slot.")
        
        # If the slot is EXPIRED, CANCELLED, or its PENDING hold time has passed, delete it to allow re-booking
        if existing_booking.status in ["EXPIRED", "CANCELLED"] or (existing_booking.status == "PENDING" and existing_booking.expires_at < now):
            logger.info(f"Releasing/cleaning up stale booking ID {existing_booking.id} to allow new hold.")
            db.delete(existing_booking)
            db.commit()
        elif existing_booking.status in ["PENDING", "CONFIRMED"]:
            logger.warning(f"Slot conflict: already held or confirmed by booking ID {existing_booking.id}.")
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "SLOT_ALREADY_BOOKED",
                    "message": "The selected slot is currently held or already confirmed by another user."
                }
            )

    try:
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
        logger.info(f"Successfully created PENDING hold with booking ID {new_booking.id}, expiring at {expires_at}")
        return new_booking
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Concurrency conflict / Integrity error during hold insertion: {str(e)}")
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "CONCURRENT_BOOKING_CONFLICT",
                "message": "Slot was acquired by another concurrent request."
            }
        )

def confirm_booking_payment(db: Session, booking_id: int) -> Booking:
    """
    BR-BOOK-02: State transition from PENDING to CONFIRMED.
    Ensures payment confirmation cannot happen on EXPIRED or CANCELLED bookings.
    """
    logger.info(f"Attempting to confirm payment for booking ID {booking_id}")
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        logger.warning(f"Booking ID {booking_id} not found for confirmation.")
        raise HTTPException(
            status_code=404,
            detail={"error_code": "BOOKING_NOT_FOUND", "message": f"Booking {booking_id} not found."}
        )

    now = datetime.utcnow()
    if booking.status == "PENDING" and booking.expires_at and booking.expires_at < now:
        logger.warning(f"Booking ID {booking_id} hold expired at {booking.expires_at}. Marking as EXPIRED.")
        booking.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={"error_code": "HOLD_EXPIRED", "message": "Booking hold duration expired before payment was completed."}
        )

    if booking.status != "PENDING":
        logger.warning(f"Invalid state transition attempt on booking ID {booking_id} with status {booking.status}")
        raise HTTPException(
            status_code=400,
            detail={"error_code": "INVALID_STATE_TRANSITION", "message": f"Cannot confirm booking in state {booking.status}."}
        )

    booking.status = "CONFIRMED"
    booking.expires_at = None
    db.commit()
    db.refresh(booking)
    logger.info(f"Booking ID {booking_id} successfully confirmed.")
    return booking

def expire_stale_holds(db: Session) -> int:
    """
    BR-BOOK-03 (Challenge 3B Expiry Job): Reclaims slots held beyond expiration time.
    """
    now = datetime.utcnow()
    stale_bookings = db.query(Booking).filter(
        Booking.status == "PENDING",
        Booking.expires_at < now
    ).all()

    count = len(stale_bookings)
    for b in stale_bookings:
        logger.info(f"Background Expiry Job: Releasing expired slot hold for booking ID {b.id} (Turf {b.turf_id}, Slot {b.start_time})")
        b.status = "EXPIRED"

    if count > 0:
        db.commit()

    return count