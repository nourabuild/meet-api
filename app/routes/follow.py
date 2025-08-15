"""Follow Routes
=============
Endpoints for managing follow relationships between users.

Endpoints:
- POST /follow/{user_id}: Follow a user.
- POST /unfollow/{user_id}: Unfollow a user.
- GET /following: Get list of users the current user follows.
- GET /followers: Get list of users who follow the current user.
- GET /status/{user_id}: Get mutual follow status with another user.
- GET /status/{user_id}/count: Get follower and following counts for a user.
"""

import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.utils.delegate import CurrentUser, FollowServiceDep
from app.utils.models import (
    FollowerListPublic,
    FollowerRelation,
    FollowCountStatus,
    FollowingListPublic,
    FollowingRelation,
    FollowStatus,
    Message,
    UserPublic,
)

router = APIRouter()

@router.post("/{user_id}/start", response_model=Message)
def follow_user(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> Message:
    """Follow a user"""
    try:
        follow_service.follow_user(current_user.id, user_id)
        response.status_code = status.HTTP_200_OK
        return Message(message="FOLLOW_SUCCESSFUL")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/stop", response_model=Message)
def unfollow_user(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> Message:
    """Unfollow a user"""
    success = follow_service.unfollow_user(current_user.id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow relationship not found",
        )

    response.status_code = status.HTTP_200_OK
    return Message(message="UNFOLLOW_SUCCESSFUL")


@router.get("/me/following/list", response_model=FollowingListPublic)
def get_my_following(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
    response: Response = None,
):
    """Get current user's following list"""
    results = follow_service.get_following_list(current_user.id, skip, limit)

    formatted = [
        FollowingRelation(
            id=follow.id,
            following_id=follow.following_id,
            user=UserPublic.model_validate(user),
            created_at=follow.created_at,
            updated_at=follow.updated_at,
        )
        for follow, user in results
    ]

    response.status_code = status.HTTP_200_OK
    return FollowingListPublic(data=formatted, count=len(formatted))


@router.get("/me/followers/list", response_model=FollowerListPublic)
def get_my_followers(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
    response: Response = None,
) -> FollowerListPublic:
    """Get current user's followers list"""
    results = follow_service.get_followers_list(current_user.id, skip, limit)

    formatted = [
        FollowerRelation(
            id=follow.id,
            follower_id=follow.follower_id,
            user=UserPublic.model_validate(user),
            created_at=follow.created_at,
            updated_at=follow.updated_at,
        )
        for follow, user in results
    ]

    response.status_code = status.HTTP_200_OK
    return FollowerListPublic(data=formatted, count=len(formatted))


@router.get("/status/{user_id}", response_model=FollowStatus)
def get_follow_status(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> FollowStatus:
    """Get follow status of a user"""
    response.status_code = status.HTTP_200_OK
    return follow_service.get_follow_status(current_user.id, user_id)


@router.get("/{user_id}/stats/view", response_model=FollowCountStatus)
def get_follow_counts(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    response: Response,
) -> FollowCountStatus:
    """Get follower and following counts for a specific user"""
    response.status_code = status.HTTP_200_OK
    return follow_service.get_follow_counts(user_id)


