from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "turf-service"
    PORT: int = 8001
    DATABASE_URL: str = "sqlite:///./turf_service.db"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
