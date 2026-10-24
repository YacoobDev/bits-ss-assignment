import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

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

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "UP"

def test_send_notification_success():
    payload = {
        "booking_id": 1,
        "user_id": "usr_100",
        "channel": "EMAIL",
        "recipient": "player@example.com",
        "message": "Your turf booking is confirmed!"
    }
    res = client.post("/api/v1/notifications/send", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "SENT"
    assert data["channel"] == "EMAIL"
