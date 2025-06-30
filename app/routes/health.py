from fastapi import APIRouter
from sqlmodel import text

from app.utils.delegate import SessionDep

router = APIRouter()


@router.get("/liveness")
def health_check() -> bool:
    """Ensure the service is running"""
    return True


@router.get("/readiness")
def readiness_check(session: SessionDep) -> bool:
    """Ensure the service is ready to handle requests"""
    session.exec(text("SELECT 1"))
    return True
