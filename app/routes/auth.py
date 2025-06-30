from datetime import timedelta

from fastapi import APIRouter, Form, HTTPException, status

from app.utils import security
from app.utils.config import settings
from app.utils.delegate import UserServiceDep
from app.utils.models import (
    EmailPasswordLogin,
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
    """Authenticate user with email and password"""
    user = user_service.authenticate(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id)

    return TokenWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/register")
def register_user(
    user_service: UserServiceDep,
    name: str = Form(...),
    account: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
) -> UserPublic:
    """Register a new user"""
    if password != password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    user_in = UserRegister(
        name=name,
        account=account,
        email=email,
        password=password
    )

    try:
        return user_service.register_user(user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/token")
def refresh_access_token(request: RefreshTokenRequest) -> Token:
    """Get a new access token"""
    user_id = security.verify_refresh_token(request.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user_id, expires_delta=access_token_expires)

    return Token(access_token=access_token)

# @router.post("/login/test-token", response_model=Message)
# def test_token(current_user: CurrentUser) -> Message:
#     """Test access token."""
#     return Message(message="Token is valid")
