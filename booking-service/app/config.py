from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "booking-service"
    PORT: int = 8002
    DATABASE_URL: str = "sqlite:///./booking_service.db"
    LOG_LEVEL: str = "INFO"
    TURF_SERVICE_URL: str = "http://localhost:8001"
    HOLD_DURATION_SECONDS: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
