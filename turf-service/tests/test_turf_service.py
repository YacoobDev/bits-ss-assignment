import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time, date

from app.main import app
from app.database import Base, get_db
from app.services.turf_logic import validate_operating_hours, generate_hourly_slots

# Setup in-memory SQLite for testing
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

# Unit Tests for Core Business Rules
def test_br_turf_01_invalid_operating_hours():
    """BR-TURF-01: Closing time before opening time must raise 400 error."""
    with pytest.raises(Exception) as exc_info:
        validate_operating_hours(time(22, 0), time(8, 0))
    assert exc_info.value.status_code == 400

def test_br_turf_02_hourly_slot_generation():
    """BR-TURF-02: Slots generated between 06:00 and 09:00 should yield 3 slots."""
    slots = generate_hourly_slots(time(6, 0), time(9, 0), 1000.0)
    assert len(slots) == 3
    assert slots[0].start_time == time(6, 0)
    assert slots[0].end_time == time(7, 0)
    assert slots[2].end_time == time(9, 0)

# API Endpoint Tests
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"

def test_create_and_get_venue():
    payload = {
        "name": "Arena One",
        "address": "456 Stadium Road",
        "city": "Chennai",
        "opening_time": "06:00:00",
        "closing_time": "22:00:00"
    }
    res = client.post("/api/v1/venues", json=payload)
    assert res.status_code == 201
    venue_id = res.json()["id"]

    res_get = client.get(f"/api/v1/venues/{venue_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Arena One"
