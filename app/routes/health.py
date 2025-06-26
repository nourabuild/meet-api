from fastapi import APIRouter
from sqlmodel import text

from app.utils.delegate import SessionDep

router = APIRouter()


@router.get("/liveness")
def health_check() -> bool:
    return True


@router.get("/readiness")
def readiness_check(session: SessionDep) -> bool:
    session.exec(text("SELECT 1"))
    return True
