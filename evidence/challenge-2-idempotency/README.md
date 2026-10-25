# Challenge 2: Idempotency Implementation & Live HTTP Test Suite

## Overview
This package contains `test_idempotency.py` updated with the required schema fields (`address` and `city`) for `/api/v1/venues`. It performs live HTTP API calls (`httpx`) against `http://localhost:8002/api/v1/venues` and logs all actions to `response_logs.txt`.

## Running Tests
Execute the test script against your running `turf-service`:
```bash
python challenge-2-idempotency/test_idempotency.py
```
