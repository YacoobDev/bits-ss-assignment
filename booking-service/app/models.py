from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime, UniqueConstraint
from datetime import datetime
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    turf_id = Column(Integer, nullable=False)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="PENDING")  # PENDING, CONFIRMED, CANCELLED, EXPIRED
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Enforce database-level uniqueness across turf, date, and start time to prevent double booking
    __table_args__ = (
        UniqueConstraint('turf_id', 'booking_date', 'start_time', name='_turf_slot_uc'),
    )
