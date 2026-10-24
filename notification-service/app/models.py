from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String, unique=True, index=True, nullable=False)
    booking_id = Column(Integer, nullable=False)
    user_id = Column(String, nullable=False)
    channel = Column(String, nullable=False)  # EMAIL, SMS
    recipient = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)  # SENT, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
