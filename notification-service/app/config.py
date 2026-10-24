from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "notification-service"
    PORT: int = 8004
    DATABASE_URL: str = "sqlite:///./notification_service.db"
    LOG_LEVEL: str = "INFO"
    MOCK_SIMULATE_SLOW_SMS: float = 0.0
    MOCK_SIMULATE_EMAIL_FAILURE: float = 0.0

    class Config:
        env_file = ".env"

settings = Settings()
