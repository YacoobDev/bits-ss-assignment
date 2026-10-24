from sqlalchemy import Column, Integer, String, Float, Time, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    opening_time = Column(Time, nullable=False)  # e.g., 06:00:00
    closing_time = Column(Time, nullable=False)  # e.g., 23:00:00

    turfs = relationship("Turf", back_populates="venue", cascade="all, delete-orphan")


class Turf(Base):
    __tablename__ = "turfs"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Turf A (7-a-side)"
    sport_type = Column(String, nullable=False)  # e.g., "Football", "Cricket"
    hourly_rate = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    venue = relationship("Venue", back_populates="turfs")
