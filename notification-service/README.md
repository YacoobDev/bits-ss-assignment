# Notification Service (Mock)

Component of the Turf Booking Microservices Application for Scalable Services (SEZG583).

## Features & Assignment Requirements Satisfied
- **Slow/Failing Dependency (Condition E):** Acts as a mock SMS/Email notification provider. Configurable settings allow simulating network delays and transient delivery failures.
- **Database Isolation:** Database-per-service pattern operating on isolated SQLite DB (`notification_service.db`).
- **Audit Log:** Stores notification audit logs for sent emails and SMS notifications.
- **Observability:** Exposes `GET /health` and propagates `X-Correlation-ID` across structured JSON logging.

## How to Run

### Local Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env # On Windows: copy .env.example .env
uvicorn app.main:app --port 8004 --reload
```

### Running Tests
```bash
pytest
```

### Swagger Documentation
Navigate to `http://localhost:8004/docs` or `http://localhost:8004/openapi.json`.
