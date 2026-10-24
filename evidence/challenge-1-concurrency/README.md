# Challenge 1: Concurrency Control & Zero Double-Booking

## Design Claim
Under high-concurrency conditions, simultaneous requests attempting to reserve the exact same turf slot (same venue, turf ID, booking date, and start time) must never over-allocate or result in double bookings. 

Our system guarantees that:
1. Exactly **1 request** acquires the lock and succeeds (`HTTP 200 OK`).
2. All remaining **19 concurrent requests** are safely rejected with `HTTP 409 Conflict`.
3. The database state remains strictly consistent with exactly **1 row record** written to `booking.db`.

---

## Evidence Mapping
* **`test_concurrency.py`**: Automated testing script using `asyncio` and `httpx` firing 20 simultaneous HTTP POST requests at `http://localhost:8002/api/v1/bookings/hold`.
* **`console_output.txt`**: Real-time terminal log capturing request execution, individual HTTP status codes, and summary validation metrics.
* **`db_state_proof.txt`**: Direct SQLite database dump from `booking.db` proving that exactly 1 booking record exists for the targeted slot.

---

## Theoretical Analysis: Why Plain Check-Then-Update Fails
A standard naive application check suffers from a **Time-of-Check to Time-of-Use (TOCTOU)** race condition:

```python
# NAIVE APPLICATION CHECK (BUGGY)
existing = db.query(Booking).filter_by(turf_id=1, date="2026-10-24", start_time="18:00:00").first()
if not existing:
    # --- RACE WINDOW ---
    new_booking = Booking(...)
    db.add(new_booking)
    db.commit()
```

When 20 concurrent threads execute `filter_by(...)` simultaneously, all 20 threads read `existing = None` before any thread commits its insert. Consequently, all 20 threads enter the conditional block and create duplicate records.

### Our Solution
1. **Database Composite Unique Index**: A composite unique constraint on `(turf_id, booking_date, start_time)` at the database storage engine layer.
2. **Pessimistic Row Locking (`SELECT FOR UPDATE`)**: Enforces atomic lock acquisition during slot evaluation, transforming duplicate insert attempts into `IntegrityError` exceptions that map to clean `HTTP 409 Conflict` client responses.
