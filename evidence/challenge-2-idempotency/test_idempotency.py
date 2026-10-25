import pytest
from fastapi.testclient import TestClient
import concurrent.futures
import uuid
import os
from datetime import datetime
from app.main import app

client = TestClient(app)

LOG_FILE = os.path.join(os.path.dirname(__file__), "response_logs.txt")

def log_event(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    log_line = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

def test_idempotent_request_success():
    key = str(uuid.uuid4())
    payload = {
        "name": "Arena Sports Complex",
        "location": "Downtown",
        "opening_time": "08:00:00",
        "closing_time": "22:00:00"
    }
    
    log_event(f"[INFO] [Idempotency] Initial request sent with key={key}, path=/api/v1/venues, payload={payload}")
    # First call
    response_1 = client.post("/api/v1/venues", json=payload, headers={"Idempotency-Key": key})
    assert response_1.status_code == 201
    data_1 = response_1.json()
    log_event(f"[INFO] [Idempotency] Initial response stored for key={key}: Status 201, Body={data_1}")

    # Second call (replay)
    log_event(f"[INFO] [Idempotency] Replay request sent with key={key}")
    response_2 = client.post("/api/v1/venues", json=payload, headers={"Idempotency-Key": key})
    assert response_2.status_code == 201
    assert response_2.json() == data_1
    log_event(f"[INFO] [Idempotency] Replay response returned for key={key}: Status 201, Cached Body={response_2.json()}")

def test_idempotency_payload_mismatch():
    key = str(uuid.uuid4())
    payload_1 = {
        "name": "Arena Sports Complex 1",
        "location": "Downtown",
        "opening_time": "08:00:00",
        "closing_time": "22:00:00"
    }
    payload_2 = {
        "name": "Arena Sports Complex 2",
        "location": "Uptown",
        "opening_time": "08:00:00",
        "closing_time": "22:00:00"
    }
    
    log_event(f"[INFO] [Idempotency] Initial request sent for conflict test with key={key}")
    response_1 = client.post("/api/v1/venues", json=payload_1, headers={"Idempotency-Key": key})
    assert response_1.status_code == 201
    log_event(f"[INFO] [Idempotency] Initial request processed for key={key}: Status 201")

    log_event(f"[INFO] [Idempotency] Mismatched payload request sent with key={key}")
    response_2 = client.post("/api/v1/venues", json=payload_2, headers={"Idempotency-Key": key})
    assert response_2.status_code == 409
    log_event(f"[WARNING] [Idempotency] Conflict detected for key={key}: Payload mismatch. Status 409")

def test_concurrent_identical_requests():
    key = str(uuid.uuid4())
    payload = {
        "name": "Concurrent Arena",
        "location": "Midtown",
        "opening_time": "08:00:00",
        "closing_time": "22:00:00"
    }

    log_event(f"[INFO] [Idempotency] Starting 5 concurrent requests with key={key}")

    def make_request(idx):
        res = client.post("/api/v1/venues", json=payload, headers={"Idempotency-Key": key})
        log_event(f"[INFO] [Idempotency] Concurrent request {idx} completed with status={res.status_code}")
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, 6)]
        results = [f.result() for f in futures]

    status_codes = [r.status_code for r in results]
    assert all(code == 201 for code in status_codes)
    
    first_json = results[0].json()
    for r in results[1:]:
        assert r.json() == first_json
    log_event(f"[INFO] [Idempotency] Concurrent test finished successfully. All 5 requests returned identical payload.")
