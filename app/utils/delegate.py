"""Dependency Injection and Authentication
=======================================
Defines FastAPI dependencies for database sessions, JWT-based user
authentication, and service/repository injections for user, follow,
and meeting domains.
"""

from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.services.agent.agent_service import AgentService
from app.services.calendar.calendar_repository import CalendarRepository
from app.services.calendar.calendar_service import CalendarService
from app.services.follow.follow_repository import FollowRepository
from app.services.follow.follow_service import FollowService
from app.services.meeting.meeting_repository import MeetingRepository
from app.services.meeting.meeting_service import MeetingService
from app.services.user.user_repository import UserRepository
from app.services.user.user_service import UserService
from app.utils import security
from app.utils.config import settings
from app.utils.models import TokenPayload, User
from app.utils.sqldb import engine

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_user_repository(session: SessionDep) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Get user service dependency."""
    return UserService(repository)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_follow_repository(session: SessionDep) -> FollowRepository:
    """Get follow repository dependency."""
    return FollowRepository(session)


def get_follow_service(
    repository: Annotated[FollowRepository, Depends(get_follow_repository)],
) -> FollowService:
    """Get follow service dependency."""
    return FollowService(repository)


FollowRepositoryDep = Annotated[FollowRepository, Depends(get_follow_repository)]
FollowServiceDep = Annotated[FollowService, Depends(get_follow_service)]


def get_meeting_repository(session: SessionDep) -> MeetingRepository:
    """Get meeting repository dependency."""
    return MeetingRepository(session)


def get_meeting_service(
    repository: Annotated[MeetingRepository, Depends(get_meeting_repository)],
) -> MeetingService:
    """Get meeting service dependency."""
    return MeetingService(repository)


MeetingRepositoryDep = Annotated[MeetingRepository, Depends(get_meeting_repository)]
MeetingServiceDep = Annotated[MeetingService, Depends(get_meeting_service)]


def get_calendar_repository(session: SessionDep) -> CalendarRepository:
    """Get calendar repository dependency."""
    return CalendarRepository(session)


def get_calendar_service(
    repository: Annotated[CalendarRepository, Depends(get_calendar_repository)],
) -> CalendarService:
    """Get calendar service dependency."""
    return CalendarService(repository)


CalendarRepositoryDep = Annotated[CalendarRepository, Depends(get_calendar_repository)]
CalendarServiceDep = Annotated[CalendarService, Depends(get_calendar_service)]


def get_agent_service(
    user_service: UserServiceDep,
    meeting_service: MeetingServiceDep,
    calendar_service: CalendarServiceDep,
    follow_service: FollowServiceDep,
) -> AgentService:
    """Get agent service dependency (singleton)."""
    return AgentService(user_service, meeting_service, calendar_service, follow_service)


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]


