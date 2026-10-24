# Booking Service

Component of the Turf Booking Microservices Application for Scalable Services (SEZG583).

## Key Features & Assignment Criteria Satisfied
- **Contended Resource & Concurrency Control (Challenge 1):** Slot bookings enforce pessimistic row locking (`with_for_update`) or unique constraints on `(turf_id, booking_date, start_time)` to ensure simultaneous requests never double-book the same slot.
- **Time-Bound Holds (Challenge 3B):** Selecting/holding a slot reserves it in `PENDING` status with an expiration timestamp (`30 seconds` by default). An automated background worker routinely scans and releases expired holds.
- **Database Isolation:** Database-per-service pattern using SQLAlchemy (`booking_service.db` default).
- **GET /health:** Standard health check endpoint for monitoring.
- **Structured JSON Logging:** Traceability across services using `X-Correlation-ID`.

## How to Run

### Local Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env # On Windows: copy .env.example .env
uvicorn app.main:app --port 8002 --reload
```

### Running Tests
```bash
pytest
```

### Swagger Documentation
Navigate to `http://localhost:8002/docs` or `http://localhost:8002/openapi.json`.
