import asyncio
import httpx
import uuid
import os
import sys
from datetime import datetime, timedelta

# Point to your live running service URL (matching test_concurrency.py)
BASE_URL = "http://localhost:8002"
BOOKING_SERVICE_URL = f"{BASE_URL}/api/v1/bookings/hold"

LOG_FILE = os.path.join(os.path.dirname(__file__), "response_logs.txt")

def log_event(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    log_line = f"[{timestamp}] {message}\n"
    # Write to response_logs.txt in append mode
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

async def run_time_bound_holds_test():
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    payload = {
        "turf_id": 1,
        "user_id": "user_hold",
        "booking_date": future_date,
        "start_time": "18:00:00",
        "end_time": "19:00:00",
        "amount": 1200.0
    }

    header_banner = (
        "============================================================\n"
        f" STARTING LIVE TIME-BOUND HOLDS & CONFLICT TEST ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
        f" Target Endpoint: {BOOKING_SERVICE_URL}\n"
        "============================================================\n"
    )
    
    print(header_banner)
    log_event(header_banner.strip())

    async with httpx.AsyncClient(timeout=10.0) as client:
        # --- TEST 1: Initial Hold Request (PENDING state creation) ---
        headers_1 = {
            "Content-Type": "application/json",
            "X-Correlation-ID": f"time-bound-hold-req-{uuid.uuid4().hex[:8]}"
        }
        
        log_event(f"[INFO] [TimeBoundHolds] Sending live POST request to {BOOKING_SERVICE_URL}")
        log_event(f"[INFO] [TimeBoundHolds] Payload: {payload}")
        log_event(f"[INFO] [TimeBoundHolds] Headers: {headers_1}")

        res_1 = await client.post(BOOKING_SERVICE_URL, json=payload, headers=headers_1)
        console_msg_1 = f"Req #1 (Initial Hold): Status {res_1.status_code} | Body: {res_1.text}"
        print(console_msg_1)
        log_event(f"[INFO] [TimeBoundHolds] Initial Hold Result -> Status: {res_1.status_code}, Body: {res_1.text}")
        
        assert res_1.status_code in (200, 201), f"Expected 200/201, got {res_1.status_code}"

        # --- TEST 2: Concurrent/Duplicate Hold Request on Locked Slot (409 Conflict) ---
        headers_2 = {
            "Content-Type": "application/json",
            "X-Correlation-ID": f"time-bound-hold-req-{uuid.uuid4().hex[:8]}"
        }
        
        log_event(f"[INFO] [TimeBoundHolds] Sending second concurrent hold request on locked slot...")
        log_event(f"[INFO] [TimeBoundHolds] Headers: {headers_2}")

        res_2 = await client.post(BOOKING_SERVICE_URL, json=payload, headers=headers_2)
        console_msg_2 = f"Req #2 (Conflict Hold): Status {res_2.status_code} | Body: {res_2.text}"
        print(console_msg_2)
        log_event(f"[WARNING] [TimeBoundHolds] Conflict Hold Result -> Status: {res_2.status_code}, Body: {res_2.text}")
        
        assert res_2.status_code == 409, f"Expected 409 Conflict, got {res_2.status_code}"

    footer_banner = (
        "============================================================\n"
        " [SUCCESS] LIVE TIME-BOUND HOLDS & CONFLICT TEST PASSED!\n"
        " Log appended to response_logs.txt successfully.\n"
        "============================================================\n"
    )
    print(footer_banner)
    log_event(footer_banner.strip())

if __name__ == "__main__":
    asyncio.run(run_time_bound_holds_test())
