from fastapi import APIRouter, HTTPException, Query, status

from app.utils.delegate import CurrentUser, UserServiceDep
from app.utils.models import Message, UserPublic, UsersPublic, UserUpdate

router = APIRouter()


@router.get("/me")
def get_user_me(current_user: CurrentUser) -> UserPublic:
    """Get current user info"""
    return current_user


@router.get("/{account}")
def get_user_by_account(
    account: str,
    user_service: UserServiceDep,
    _: CurrentUser
) -> UserPublic:
    """Get user by account"""
    user = user_service.get_user_by_account(account)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.get("/search")
def search_users(
    user_service: UserServiceDep,
    _: CurrentUser,
    q: str = Query(..., min_length=2),
    skip: int = 0,
    limit: int = 20
) -> UsersPublic:
    """Search users"""
    return user_service.search_users(q, skip, limit)


@router.post("/delete")
def soft_delete_user(
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> Message:
    """Soft delete current user"""
    try:
        user_service.soft_delete_user(current_user.id)
        return Message(message="SCHEDULED_FOR_DELETION")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/recover")
def recover_user_account(
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> Message:
    """Recover user account"""
    success = user_service.recover_user(current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot recover account."
        )

    return Message(message="Account successfully recovered!")


@router.post("/update")
def update_user_profile(
    user_service: UserServiceDep,
    user_in: UserUpdate,
    current_user: CurrentUser
) -> UserPublic:
    """Update current user profile"""
    try:
        return user_service.update_user(current_user.id, user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
