from fastapi import APIRouter, HTTPException, Query

from app.utils.config import settings
from app.utils.delegate import CurrentUser, UserServiceDep
from app.utils.models import Message, UserPublic, UsersPublic, UserUpdate

router = APIRouter()


@router.get("/me")
def get_user_me(current_user: CurrentUser) -> UserPublic:
    """Get current user profile (only accessible after login)."""
    return current_user


@router.get("/search")
def search_users(
    user_service: UserServiceDep,
    current_user: CurrentUser,
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = 0,
    limit: int = 20
) -> UsersPublic:
    """Search users (only accessible after login)."""
    return user_service.search_users(q, skip, limit)



@router.get("/deletion-info")
def get_deletion_info(
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> dict:
    """Get information about account deletion status."""
    try:
        result = user_service.get_user_deletion_info(current_user.id)
        print(f"DEBUG: Service returned: {result}")
        return result
    except ValueError as e:
        print(f"DEBUG: ValueError caught: {e!s}")
        # If user not found in deletion info lookup, return default state
        return {
            "is_scheduled_for_deletion": False,
            "deleted_at": None,
            "days_until_permanent_deletion": None,
            "can_recover": False
        }


@router.get("/{account}")
def get_user_by_account(
    account: str,
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> UserPublic:
    """Get user by account name (only accessible after login)."""
    user = user_service.get_user_by_account(account)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user


@router.post("/delete")
def soft_delete_user(
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> Message:
    """Soft delete current user (configurable recovery period)."""
    try:
        user_service.soft_delete_user(current_user.id)
        return Message(message=f"User scheduled for deletion. You have {settings.USER_DELETION_GRACE_PERIOD_DAYS} days to recover your account.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/regular-delete")
def delete_user(
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> Message:
    """Regular delete current user (no recovery period)."""
    try:
        user_service.delete_user(current_user.id)
        return Message(message="User deleted successfully.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/recover")
def recover_user_account(
    user_service: UserServiceDep,
    current_user: CurrentUser
) -> Message:
    """Recover user account if within recovery period."""
    success = user_service.recover_user(current_user.id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot recover account. Either not scheduled for deletion or recovery period has expired."
        )
    return Message(message="Account successfully recovered!")


@router.post("/update")
def update_user_profile(
    user_service: UserServiceDep,
    user_in: UserUpdate,
    current_user: CurrentUser
) -> UserPublic:
    """Update current user profile (only accessible after login)."""
    try:
        return user_service.update_user(current_user.id, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
