# Challenge 3B: Time-Bound Holds Test Script & Logs

## Overview
This package contains `test_time_bound_holds.py` configured with automated real-time logging. Every time the test script is executed against your running `turf-service` instance (`http://localhost:8002/api/v1/bookings/hold`), it performs live HTTP requests and automatically logs all request payloads, HTTP response statuses, booking IDs, error details, and timestamped events into `response_logs.txt`.

## Running Tests
Execute the live test script against your running turf-service instance:
```bash
python challenge-3b-time-bound-holds/test_time_bound_holds.py
```
