from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "payment-service"
    PORT: int = 8003
    DATABASE_URL: str = "sqlite:///./payment_service.db"
    LOG_LEVEL: str = "INFO"
    MOCK_LATENCY_SECONDS: float = 0.5
    MOCK_FAILURE_RATE: float = 0.0

    class Config:
        env_file = ".env"

settings = Settings()
