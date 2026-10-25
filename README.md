# bits-ss-assignment
Bits Scalable services assignment

# Turf Slot Booking Microservice Architecture & Challenges

## 1. Overview of the Four Services
The architecture is structured around modular microservices to cleanly separate domains, ensure transactional isolation, and scale independently:

* **Booking Service (`/api/v1/bookings`)**: Manages slot lifecycle operations, including holding slots, confirming bookings, retrieving user booking histories, and executing atomic concurrency controls.
* **Turf Management Service (`/api/v1/turfs`)**: Handles turf venue administration, location info, pricing, and incorporates idempotency controls for venue creation.
* **Idempotency & Replay Service**: A cross-cutting utility layer that intercepts mutating requests via `Idempotency-Key` headers, performs SHA-256 request payload fingerprinting, and manages response caching to protect against duplicate actions.
* **Background Expiration Worker (Challenge 3B)**: A dedicated time-bound hold manager that periodically monitors or lazily purges expired `PENDING` slots, automatically rolling them back to the available pool when TTLs expire.

---

## 2. Challenge Breakdown & Solutions

### Challenge 1: Concurrency & Slot Availability
* **The Problem**: High-contention prime slots (such as weekend evenings or night slots under lights) face massive spikes. If 20 players attempt to book the exact same Saturday 7:00 PM slot simultaneously, classic race conditions (TOCTOU) can lead to double-booking.
* **The Solution**: 
  - Backed by database-level **Unique Constraints** (`_turf_slot_uc` on `turf_id`, `booking_date`, and `start_time`).
  - Strict transaction atomicity ensures that when parallel requests arrive at the exact same millisecond, **exactly one request succeeds (`201 Created`)** while the other 19 fail gracefully with a `409 Conflict` (`SLOT_ALREADY_BOOKED`).

### Challenge 2: Idempotency on Turf Creation (`challenge-2-idempotency`)
* **The Problem**: Network glitches, client retries, or accidental double-clicks can cause unsafe mutating requests (like creating a new turf venue) to be sent multiple times.
* **The Solution**:
  - Clients provide a unique UUID via the **`Idempotency-Key` header**.
  - The server computes a deterministic **SHA-256 cryptographic fingerprint** of the JSON request body and stores it alongside the key and response in the `idempotency_records` table.
  - **Sequential Repeats**: Subsequent requests with the same key instantly replay the cached response without re-running business logic.
  - **Payload Mismatch Protection**: Reusing the same key with a modified payload is immediately rejected with an HTTP `409 Conflict`.
  - **Concurrent Safety**: When multiple identical requests arrive simultaneously, database locks ensure that only one actual venue creation occurs while all concurrent callers receive the identical `201 Created` response status and matching payload.

### Challenge 3B: Time-Bound Holds (`challenge-3b-time-bound-holds`)
* **The Problem**: Users frequently hold prime slots while entering payment details but abandon the page or let timers run out, locking up inventory indefinitely.
* **The Solution**:
  - When a user initiates a slot hold, the system assigns a strict **30-second TTL** (`expires_at = now + 30s`) with a `PENDING` status.
  - If the user completes payment, the status updates to `CONFIRMED`.
  - If they abandon the payment page or let the timer run out, background expiration checks or lazy-purge routines automatically release the slot back to the available pool so other players can instantly book it.

---

## 3. How to Execute Each Service & Test Suite

Follow these instructions to spin up the backend and run the validation scripts for each component:

### Step 1: Start the FastAPI Backend Application
Open a terminal in your project root directory and start the Uvicorn server:
```bash
uvicorn app.main:app --reload --port 8002
```
*(The server will initialize database tables automatically and listen on port `8002`)*.

---

### Step 2: Execute Challenge 1 (Concurrency Stress Test)
To verify that high-contention slot bookings handle 20 simultaneous requests safely (1 success, 19 conflicts):
1. Navigate to your Challenge 1 test directory or root script location.
2. Run the concurrency test script:
   ```bash
   python test_concurrency.py
   ```

---

### Step 3: Execute Challenge 2 (Idempotency Suite)
To verify sequential replays, payload mismatch protections (`409 Conflict`), and concurrent identical requests on turf creation:
1. Navigate to the `challenge-2-idempotency/` folder:
   ```bash
   cd challenge-2-idempotency
   ```
2. Run the test script:
   ```bash
   python test_idempotency.py
   ```
3. Check **`response_logs.txt`** in the same folder to review the auto-generated live execution logs and test assertions.

---

### Step 4: Execute Challenge 3B (Time-Bound Hold & Expiration Check)
To test 30-second slot TTL expiration and automatic inventory release:
1. Hold a slot via a booking request.
2. Wait 30 seconds for the expiration TTL to pass (or check backend logs as lazy-purges/background sweeps run).
3. Attempt to book the same slot again to verify it has been successfully returned to the available pool.