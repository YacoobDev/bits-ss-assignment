from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import json

from app.database import get_db, SessionLocal
from app.models import Venue, Turf, IdempotencyRecord
from app.schemas import VenueCreate, VenueResponse, TurfCreate, TurfResponse, SlotAvailabilityResponse, TimeSlot
from app.services.turf_logic import validate_operating_hours, generate_hourly_slots
from app.idempotency import check_idempotency

router = APIRouter(prefix="/api/v1", tags=["Venues & Turfs"])

@router.post("/venues", response_model=VenueResponse, status_code=201)
async def create_venue(request: Request, response: Response, venue_in: VenueCreate, db: Session = Depends(get_db)):
    # 1. Check idempotency
    idempotency_result = await check_idempotency(request)
    if idempotency_result and idempotency_result.get("cached"):
        response.status_code = idempotency_result["status_code"]
        return idempotency_result["body"]

    # 2. Execute business logic
    validate_operating_hours(venue_in.opening_time, venue_in.closing_time)
    db_venue = Venue(**venue_in.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    
    # Serialize response dictionary matching VenueResponse schema
    response_body = VenueResponse.from_orm(db_venue).dict()
    # Handle serialization for dates/times if any exist, or use standard dict json conversion
    # Note: Using jsonable_encoder or custom serialization if needed, standard dict usually works fine with FastAPI/SQLAlchemy models

    # 3. Store idempotency record if key was provided
    if idempotency_result and not idempotency_result.get("cached"):
        record_db = SessionLocal()
        try:
            record = IdempotencyRecord(
                idempotency_key=idempotency_result["key"],
                request_fingerprint=idempotency_result["fingerprint"],
                response_status_code=201,
                response_body=json.dumps(response_body, default=str)
            )
            record_db.add(record)
            record_db.commit()
        except Exception:
            record_db.rollback()
        finally:
            record_db.close()

    response.status_code = 201
    return db_venue

@router.get("/venues", response_model=List[VenueResponse])
def list_venues(db: Session = Depends(get_db)):
    return db.query(Venue).all()

@router.get("/venues/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "VENUE_NOT_FOUND", "message": f"Venue with id {venue_id} not found"}
        )
    return venue

@router.post("/turfs", response_model=TurfResponse, status_code=201)
async def create_turf(request: Request, response: Response, turf_in: TurfCreate, db: Session = Depends(get_db)):
    # 1. Check idempotency
    idempotency_result = await check_idempotency(request)
    if idempotency_result and idempotency_result.get("cached"):
        response.status_code = idempotency_result["status_code"]
        return idempotency_result["body"]

    # 2. Execute business logic
    venue = db.query(Venue).filter(Venue.id == turf_in.venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "VENUE_NOT_FOUND", "message": f"Venue with id {turf_in.venue_id} not found"}
        )
    db_turf = Turf(**turf_in.dict())
    db.add(db_turf)
    db.commit()
    db.refresh(db_turf)

    response_body = TurfResponse.from_orm(db_turf).dict()

    # 3. Store idempotency record if key was provided
    if idempotency_result and not idempotency_result.get("cached"):
        record_db = SessionLocal()
        try:
            record = IdempotencyRecord(
                idempotency_key=idempotency_result["key"],
                request_fingerprint=idempotency_result["fingerprint"],
                response_status_code=201,
                response_body=json.dumps(response_body, default=str)
            )
            record_db.add(record)
            record_db.commit()
        except Exception:
            record_db.rollback()
        finally:
            record_db.close()

    response.status_code = 201
    return db_turf

@router.get("/listTurfs", response_model=List[TurfResponse])
def list_turfs(
    venue_id: Optional[int] = Query(None, description="Filter turfs by venue ID"),
    db: Session = Depends(get_db)
):
    """
    List all turfs or filter them by a specific venue_id using listTurfs.
    """
    query = db.query(Turf)
    if venue_id is not None:
        query = query.filter(Turf.venue_id == venue_id)
    
    return query.all()

@router.get("/turfs/{turf_id}", response_model=TurfResponse)
def get_turf(turf_id: int, db: Session = Depends(get_db)):
    turf = db.query(Turf).filter(Turf.id == turf_id).first()
    if not turf:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "TURF_NOT_FOUND", "message": f"Turf with id {turf_id} not found"}
        )
    return turf

@router.get("/turfs/{turf_id}/slots", response_model=SlotAvailabilityResponse)
def get_turf_slots(turf_id: int, booking_date: date = Query(...), db: Session = Depends(get_db)):
    turf = db.query(Turf).filter(Turf.id == turf_id).first()
    if not turf:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "TURF_NOT_FOUND", "message": f"Turf with id {turf_id} not found"}
        )
    
    venue = db.query(Venue).filter(Venue.id == turf.venue_id).first()
    slots = generate_hourly_slots(venue.opening_time, venue.closing_time, turf.hourly_rate)
    
    return SlotAvailabilityResponse(
        turf_id=turf_id,
        booking_date=booking_date,
        slots=slots
    )