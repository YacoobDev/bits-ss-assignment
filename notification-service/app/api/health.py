from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "UP",
        "service": settings.SERVICE_NAME
    }
