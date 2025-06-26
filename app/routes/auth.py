# Have login/register/refresh-token endpoints in app/routes/auth.py

from datetime import timedelta

from fastapi import APIRouter, Form, HTTPException

from app.utils import security
from app.utils.config import settings
from app.utils.delegate import CurrentUser, UserServiceDep
from app.utils.models import (
    EmailPasswordLogin,
    Message,
    RefreshTokenRequest,
    Token,
    TokenWithRefresh,
    UserPublic,
    UserRegister,
)

router = APIRouter()


@router.post("/login")
def login_with_email_password(
    user_service: UserServiceDep, credentials: EmailPasswordLogin
) -> TokenWithRefresh:
    """Login with email and password, get access and refresh tokens for future requests."""
    user = user_service.authenticate(credentials.email, credentials.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id)

    return TokenWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login/test-token", response_model=Message)
def test_token(current_user: CurrentUser) -> Message:
    """Test access token."""
    return Message(message="Token is valid")

@router.post("/register")
def register_user(
    user_service: UserServiceDep,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    account: str = Form(...),
    name: str = Form(...)
) -> UserPublic:
    """Register a new user account (multipart form, with password confirmation)."""
    if password != password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    user_in = UserRegister(email=email, password=password, account=account, name=name)
    try:
        return user_service.register_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh-token")
def refresh_access_token(request: RefreshTokenRequest) -> Token:
    """Get a new access token using a refresh token."""
    user_id = security.verify_refresh_token(request.refresh_token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user_id, expires_delta=access_token_expires)

    return Token(access_token=access_token)
