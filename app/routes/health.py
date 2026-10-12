from fastapi import APIRouter
from app.config import settings
from app.state import interview_store

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "app": "InterviewIQ",
        "model": settings.groq_model,
        "active_in_memory_sessions": interview_store.count(),
    }
