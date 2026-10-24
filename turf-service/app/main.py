import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import Base, engine
from app.api import health, venues
from app.logging_config import setup_logging, correlation_id_ctx
from app.config import settings

setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Turf/Venue Service",
    version="1.0.0",
    description="Microservice managing venues, turfs, and slot availability for Turf Booking system."
)

# --- ADD THIS CORS MIDDLEWARE BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allows requests from any origin (local files, dashboards, etc.)
    allow_credentials=True,
    allow_methods=["*"],       # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],       # Allows custom headers like X-Correlation-ID and Idempotency-Key
)
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    token = correlation_id_ctx.set(corr_id)
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    
    correlation_id_ctx.reset(token)
    return response

app.include_router(health.router)
app.include_router(venues.router)
