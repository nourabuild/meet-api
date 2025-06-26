import uuid

from fastapi import APIRouter, HTTPException

from app.utils.delegate import CurrentUser, FollowServiceDep
from app.utils.models import (
    FollowPublic,
    FollowerWithUserList,
    FollowsPublic,
    FollowStats,
    FollowStatus,
    Message,
    UserPublic,
    FollowingWithUserList,
)

router = APIRouter()


@router.post("/follow/{user_id}", response_model=FollowPublic)
def follow_user(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> FollowPublic:
    """Follow a user."""
    try:
        return follow_service.follow_user(current_user.id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/unfollow/{user_id}", response_model=Message)
def unfollow_user(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> Message:
    """Unfollow a user."""
    success = follow_service.unfollow_user(current_user.id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    return Message(message="Successfully unfollowed user")


# @router.get("/followers", response_model=FollowsPublic)
# def get_my_followers(
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser,
#     skip: int = 0,
#     limit: int = 20
# ) -> FollowsPublic:
#     """Get current user's followers."""
#     return follow_service.get_followers(current_user.id, skip, limit)


@router.get("/followers", response_model=FollowerWithUserList)
def get_my_followers(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
):
    results = follow_service.get_followers_with_users(current_user.id, skip, limit)
    formatted = []
    for follow, user in results:
        formatted.append({
            "id": follow.id,
            "follower_id": follow.follower_id,
            "user": UserPublic.model_validate(user),
            "created_at": follow.created_at,
            "updated_at": follow.updated_at,
        })
    return {"data": formatted, "count": len(formatted)}


@router.get("/following", response_model=FollowingWithUserList)
def get_my_following(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
):
    results = follow_service.get_following_with_users(current_user.id, skip, limit)
    formatted = []
    for follow, user in results:
        formatted.append({
            "id": follow.id,
            "following_id": follow.following_id,
            "user": UserPublic.model_validate(user),
            "created_at": follow.created_at,
            "updated_at": follow.updated_at,
        })
    return {"data": formatted, "count": len(formatted)}


@router.get("/followers/{user_id}", response_model=FollowsPublic)
def get_user_followers(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
) -> FollowsPublic:
    """Get followers for a specific user."""
    return follow_service.get_followers(user_id, skip, limit)


@router.get("/following/{user_id}", response_model=FollowsPublic)
def get_user_following(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
) -> FollowsPublic:
    """Get users that a specific user is following."""
    return follow_service.get_following(user_id, skip, limit)


@router.get("/stats", response_model=FollowStats)
def get_my_follow_stats(
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> FollowStats:
    """Get current user's follow statistics."""
    return follow_service.get_follow_stats(current_user.id)


@router.get("/stats/{user_id}", response_model=FollowStats)
def get_user_follow_stats(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> FollowStats:
    """Get follow statistics for a specific user."""
    return follow_service.get_follow_stats(user_id)


@router.get("/status/{user_id}", response_model=FollowStatus)
def get_follow_status(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> FollowStatus:
    """Get follow relationship status with a specific user."""
    return follow_service.get_follow_status(current_user.id, user_id)


@router.get("/mutual", response_model=FollowsPublic)
def get_mutual_follows(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
) -> FollowsPublic:
    """Get mutual follows (users who follow each other)."""
    return follow_service.get_mutual_follows(current_user.id, skip, limit)


@router.get("/check/{user_id}")
def check_if_following(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> dict:
    """Check if current user is following a specific user."""
    is_following = follow_service.is_following(current_user.id, user_id)
    return {"is_following": is_following}
