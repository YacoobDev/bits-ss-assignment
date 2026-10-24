import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, time as dtime

from app.main import app
from app.database import Base, get_db
from app.schemas import HoldSlotRequest
from app.services.booking_logic import hold_booking_slot, confirm_booking_payment

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_br_book_01_hold_slot_success():
    req = HoldSlotRequest(
        user_id="usr_01",
        turf_id=1,
        booking_date=date(2026, 10, 25),
        start_time=dtime(18, 0),
        end_time=dtime(19, 0),
        amount=1000.0
    )
    db = TestingSessionLocal()
    booking = hold_booking_slot(db, req)
    assert booking.status == "PENDING"
    assert booking.user_id == "usr_01"
    db.close()

def test_br_book_01_prevent_duplicate_hold():
    req = HoldSlotRequest(
        user_id="usr_02",
        turf_id=1,
        booking_date=date(2026, 10, 25),
        start_time=dtime(18, 0),
        end_time=dtime(19, 0),
        amount=1000.0
    )
    db = TestingSessionLocal()
    with pytest.raises(Exception) as exc_info:
        hold_booking_slot(db, req)
    assert exc_info.value.status_code == 409
    db.close()

def test_br_book_02_confirm_booking():
    db = TestingSessionLocal()
    booking = confirm_booking_payment(db, 1)
    assert booking.status == "CONFIRMED"
    db.close()

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "UP"
