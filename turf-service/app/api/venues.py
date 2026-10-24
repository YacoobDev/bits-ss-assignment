from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import Venue, Turf
from app.schemas import VenueCreate, VenueResponse, TurfCreate, TurfResponse, SlotAvailabilityResponse, TimeSlot
from app.services.turf_logic import validate_operating_hours, generate_hourly_slots

router = APIRouter(prefix="/api/v1", tags=["Venues & Turfs"])

@router.post("/venues", response_model=VenueResponse, status_code=201)
def create_venue(venue_in: VenueCreate, db: Session = Depends(get_db)):
    validate_operating_hours(venue_in.opening_time, venue_in.closing_time)
    db_venue = Venue(**venue_in.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
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
def create_turf(turf_in: TurfCreate, db: Session = Depends(get_db)):
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
