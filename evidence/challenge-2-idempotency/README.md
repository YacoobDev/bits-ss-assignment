# Challenge 2: Idempotency Implementation

## Overview
This implementation guarantees that unsafe HTTP requests (`POST`, `PUT`, `PATCH`, `DELETE`) accompanied by an `Idempotency-Key` header are safely executed exactly once.

## Key Features
1. **Payload Fingerprinting**: Computes a SHA-256 hash of the HTTP method, request path, and body. If a key is reused with a different payload, a **409 Conflict** is returned.
2. **Concurrent Request Protection**: Leverages database unique constraints (`idempotency_key` unique index) to handle simultaneous identical requests safely without race conditions or duplicate side effects.
3. **Response Replay**: Subsequent sequential or concurrent requests with matching keys return the identical cached response status and payload.
4. **Automated Logging**: Test execution writes real-time logs directly to `response_logs.txt`.

## Running Tests
Execute pytest against the idempotency test suite:
```bash
pytest challenge-2-idempotency/test_idempotency.py
```
