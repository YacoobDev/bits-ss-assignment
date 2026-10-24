import asyncio
import httpx
import sys

BOOKING_SERVICE_URL = "http://localhost:8002/api/v1/bookings/hold"

TARGET_PAYLOAD = {
    "turf_id": 1,
    "user_id": "concurrent_tester",
    "booking_date": "2026-10-24",
    "start_time": "18:00:00",
    "end_time": "19:00:00",
    "amount": 1200.0
}

TOTAL_PARALLEL_REQUESTS = 20

class Tee:
    """Class to duplicate stdout to both console terminal and a text file."""
    def __init__(self, filename="console_output.txt"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

async def send_booking_request(client, req_id):
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": f"concurrency-test-req-{req_id}"
    }
    try:
        response = await client.post(BOOKING_SERVICE_URL, json=TARGET_PAYLOAD, headers=headers)
        return req_id, response.status_code, response.json()
    except Exception as e:
        return req_id, 0, {"error": str(e)}

async def run_concurrency_test():
    print("============================================================")
    print(f" STARTING CONCURRENCY STRESS TEST ({TOTAL_PARALLEL_REQUESTS} Simultaneous Requests)")
    print(" Target Slot: Turf ID 1 | 2026-10-24 @ 18:00:00")
    print("============================================================\n")

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [send_booking_request(client, i + 1) for i in range(TOTAL_PARALLEL_REQUESTS)]
        results = await asyncio.gather(*tasks)

    success_count = 0
    conflict_count = 0
    other_count = 0

    print(f"{'Req #':<8} | {'Status Code':<12} | {'Response Detail / Message'}")
    print("-" * 65)

    for req_id, status_code, body in results:
        # Accept both 200 OK and 201 Created as successful allocations
        if status_code in (200, 201):
            success_count += 1
            bid = body.get("id") or body.get("booking_id")
            print(f"Req #{req_id:<4} | {status_code} SUCCESS   | SUCCESS -> Booking ID: {bid}")
        elif status_code == 409:
            conflict_count += 1
            detail = body.get("message") or body.get("detail", "Slot already locked")
            print(f"Req #{req_id:<4} | {status_code} CONFLICT  | REJECTED -> {detail}")
        else:
            other_count += 1
            print(f"Req #{req_id:<4} | {status_code} ERROR     | {body}")

    print("\n============================================================")
    print(" TEST RESULTS SUMMARY")
    print("============================================================")
    print(f" Total Requests Fired : {TOTAL_PARALLEL_REQUESTS}")
    print(f" Successful (200/201) : {success_count}  (Expected: 1)")
    print(f" Conflict (409)       : {conflict_count} (Expected: 19)")
    print(f" Other / Errors       : {other_count}")
    print("============================================================")

    if success_count == 1 and conflict_count == (TOTAL_PARALLEL_REQUESTS - 1):
        print("\n[SUCCESS] TEST PASSED: Zero double-booking confirmed under race conditions!")
    else:
        print("\n[FAILURE] TEST FAILED: Over-allocation or unhandled race condition detected.")

if __name__ == "__main__":
    # Automatically log output to console_output.txt
    sys.stdout = Tee("console_output.txt")
    asyncio.run(run_concurrency_test())