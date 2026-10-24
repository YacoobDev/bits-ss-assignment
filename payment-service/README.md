# Payment Service (Mock)

Component of the Turf Booking Microservices Application for Scalable Services (SEZG583).

## Features & Assignment Requirements Satisfied
- **Unsafe-to-Repeat Operation & Idempotency (Challenge 2):** Processes charges using an mandatory `Idempotency-Key` header. Stores key + payload fingerprint + cached response. Repeating requests returns identical responses without double charging. Mismatched payloads return HTTP 409 Conflict.
- **Flaky/Failing Mock Dependency (Condition E & Challenge 3A):** Configurable artificial latency and simulated failure rate (`MOCK_LATENCY_SECONDS`, `MOCK_FAILURE_RATE`).
- **Database-per-Service:** Isolated SQLite database (`payment_service.db`).
- **Observability:** Exposes `GET /health` and propagates `X-Correlation-ID` structured JSON logging.

## How to Run

### Local Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env # On Windows: copy .env.example .env
uvicorn app.main:app --port 8003 --reload
```

### Running Tests
```bash
pytest
```

### Swagger Documentation
Navigate to `http://localhost:8003/docs` or `http://localhost:8003/openapi.json`.
