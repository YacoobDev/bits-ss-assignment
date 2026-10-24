# Turf/Venue Service

Component of the Turf Booking Microservices Application for Scalable Services (SEZG583).

## Features
- Manages venues, turfs (pitches/courts), and slot availability.
- Database-per-service pattern using SQLAlchemy (SQLite default).
- GET /health endpoint for readiness/liveness checks.
- Structured JSON logging with `X-Correlation-ID` header propagation.
- Comprehensive unit tests covering business rules.

## How to Run

### Local Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env # On Windows: copy .env.example .env
uvicorn app.main:app --port 8001 --reload
```

### Running Tests
```bash
pytest
```

### Swagger Documentation
Once running, navigate to `http://localhost:8001/docs` or `http://localhost:8001/openapi.json`.
