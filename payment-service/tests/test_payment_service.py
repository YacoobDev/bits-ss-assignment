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

def test_charge_missing_idempotency_key():
    payload = {"booking_id": 1, "user_id": "usr_1", "amount": 1000.0}
    res = client.post("/api/v1/payments/charge", json=payload)
    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "MISSING_IDEMPOTENCY_KEY"

def test_charge_idempotency_success_and_replay():
    payload = {"booking_id": 1, "user_id": "usr_1", "amount": 1000.0}
    headers = {"Idempotency-Key": "key_test_123"}
    
    # First call
    res1 = client.post("/api/v1/payments/charge", json=payload, headers=headers)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["status"] == "SUCCESS"

    # Replay call with exact same key and payload
    res2 = client.post("/api/v1/payments/charge", json=payload, headers=headers)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data1["transaction_id"] == data2["transaction_id"]

def test_charge_idempotency_payload_mismatch():
    headers = {"Idempotency-Key": "key_test_mismatch"}
    payload1 = {"booking_id": 1, "user_id": "usr_1", "amount": 1000.0}
    payload2 = {"booking_id": 1, "user_id": "usr_1", "amount": 2000.0}
    
    client.post("/api/v1/payments/charge", json=payload1, headers=headers)
    
    # Same key, different payload -> expect 409
    res = client.post("/api/v1/payments/charge", json=payload2, headers=headers)
    assert res.status_code == 409
    assert res.json()["detail"]["error_code"] == "IDEMPOTENCY_KEY_REUSE_PAYLOAD_MISMATCH"
