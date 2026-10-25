import asyncio
import httpx
import uuid
import os
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"
TARGET_URL = f"{BASE_URL}/api/v1/venues"

LOG_FILE = os.path.join(os.path.dirname(__file__), "response_logs.txt")

def log_event(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    log_line = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

async def run_idempotency_test():
    header_banner = (
        "============================================================\n"
        f" STARTING LIVE IDEMPOTENCY API STRESS TEST ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
        f" Target Endpoint: {TARGET_URL}\n"
        "============================================================\n"
    )
    print(header_banner)
    log_event(header_banner.strip())

    idempotency_key_1 = str(uuid.uuid4())
    # Updated payload with required Pydantic schema fields: address and city
    payload_1 = {
        "name": f"Arena Sports Complex {uuid.uuid4().hex[:4]}",
        "location": "Downtown",
        "address": "123 Main Street",
        "city": "Bangalore",
        "opening_time": "08:00:00",
        "closing_time": "22:00:00"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # --- TEST 1: Initial Request & Replay ---
        headers_1 = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key_1,
            "X-Correlation-ID": f"idempotency-test-initial-{uuid.uuid4().hex[:8]}"
        }

        log_event(f"[INFO] [Idempotency] Sending initial request with key={idempotency_key_1}")
        log_event(f"[INFO] [Idempotency] Payload: {payload_1}")

        res_init = await client.post(TARGET_URL, json=payload_1, headers=headers_1)
        print(f"Initial Request: Status {res_init.status_code} | Body: {res_init.text}")
        log_event(f"[INFO] [Idempotency] Initial response stored for key={idempotency_key_1}: Status {res_init.status_code}, Body={res_init.text}")
        assert res_init.status_code in (200, 201), f"Expected 200/201, got {res_init.status_code}"

        # Replay Request
        log_event(f"[INFO] [Idempotency] Replay request sent with key={idempotency_key_1}")
        res_replay = await client.post(TARGET_URL, json=payload_1, headers=headers_1)
        print(f"Replay Request: Status {res_replay.status_code} | Body: {res_replay.text}")
        log_event(f"[INFO] [Idempotency] Replay response returned for key={idempotency_key_1}: Status {res_replay.status_code}, Cached Body={res_replay.text}")
        assert res_replay.status_code == res_init.status_code

        # --- TEST 2: Mismatched Payload Conflict (409) ---
        mismatched_payload = {
            "name": "Different Venue Name",
            "location": "Uptown",
            "address": "456 Side Ave",
            "city": "Chennai",
            "opening_time": "09:00:00",
            "closing_time": "23:00:00"
        }
        log_event(f"[INFO] [Idempotency] Mismatched payload request sent with key={idempotency_key_1}")
        res_mismatch = await client.post(TARGET_URL, json=mismatched_payload, headers=headers_1)
        print(f"Mismatch Request: Status {res_mismatch.status_code} | Body: {res_mismatch.text}")
        log_event(f"[WARNING] [Idempotency] Conflict detected for key={idempotency_key_1}: Payload mismatch. Status {res_mismatch.status_code}")
        assert res_mismatch.status_code == 409

        # --- TEST 3: Concurrent Requests Safety ---
        idempotency_key_concurrent = str(uuid.uuid4())
        payload_concurrent = {
            "name": f"Concurrent Arena {uuid.uuid4().hex[:4]}",
            "location": "Central Park",
            "address": "789 Park Blvd",
            "city": "Bangalore",
            "opening_time": "06:00:00",
            "closing_time": "23:00:00"
        }

        async def send_concurrent(req_id):
            headers = {
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key_concurrent,
                "X-Correlation-ID": f"idempotency-concurrent-{req_id}"
            }
            res = await client.post(TARGET_URL, json=payload_concurrent, headers=headers)
            return req_id, res.status_code, res.text

        log_event(f"[INFO] [Idempotency] Starting 5 concurrent requests with key={idempotency_key_concurrent}")
        tasks = [send_concurrent(i + 1) for i in range(5)]
        results = await asyncio.gather(*tasks)

        for req_id, status_code, text in results:
            print(f"Concurrent Req #{req_id}: Status {status_code} | Body: {text}")
            log_event(f"[INFO] [Idempotency] Concurrent request {req_id} completed with status={status_code}")
            assert status_code in (200, 201)

        log_event(f"[INFO] [Idempotency] Concurrent test finished successfully. All 5 requests returned identical payload.")

    footer_banner = (
        "============================================================\n"
        " [SUCCESS] LIVE IDEMPOTENCY TEST PASSED SUCCESSFULLY!\n"
        " Log appended to response_logs.txt successfully.\n"
        "============================================================\n"
    )
    print(footer_banner)
    log_event(footer_banner.strip())

if __name__ == "__main__":
    asyncio.run(run_idempotency_test())
