import uuid

from fastapi import APIRouter, HTTPException, status

from app.utils.delegate import CurrentUser, FollowServiceDep
from app.utils.models import (
    FollowStatus,
    FollowerListPublic,
    FollowerRelation,
    FollowingListPublic,
    FollowingRelation,
    Message,
    UserPublic,
)

router = APIRouter()


@router.post("/follow/{user_id}", response_model=Message)
def follow_user(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> Message:
    """Follow a user."""
    
    try:
        follow_service.follow_user(current_user.id, user_id)
        return Message(message="FOLLOW_SUCCESSFUL")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/unfollow/{user_id}", response_model=Message)
def unfollow_user(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> Message:
    """Unfollow a user."""
    success = follow_service.unfollow_user(current_user.id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow relationship not found"
        )
    
    return Message(message="UNFOLLOW_SUCCESSFUL")



@router.get("/following", response_model=FollowingListPublic)
def get_my_following(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
):
    """Get users that current user is following with user data."""
    results = follow_service.get_following_list(current_user.id, skip, limit)
    print(f"Results: {results}")
    
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
    
    return FollowingListPublic(data=formatted, count=len(formatted))

@router.get("/followers", response_model=FollowerListPublic)
def get_my_followers(
    follow_service: FollowServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20
) -> FollowerListPublic:
    """Get current user's followers with user data."""
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
    
    return FollowerListPublic(data=formatted, count=len(formatted))

@router.get("/status/{user_id}", response_model=FollowStatus)
def get_follow_status(
    user_id: uuid.UUID,
    follow_service: FollowServiceDep,
    current_user: CurrentUser
) -> FollowStatus:
    """Get follow relationship status with a specific user."""
    return follow_service.get_follow_status(current_user.id, user_id)


# ------------ HIGH PRIORITY ENDPOINTS ABOVE ------------

# @router.get("/status/{user_id}", response_model=FollowStatus)
# def get_follow_status(
#     user_id: uuid.UUID,
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser
# ) -> FollowStatus:
#     """Get follow relationship status with a specific user."""
#     return follow_service.get_follow_status(current_user.id, user_id)

# @router.get("/followers/{user_id}", response_model=FollowsPublic)
# def get_user_followers(
#     user_id: uuid.UUID,
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser,
#     skip: int = 0,
#     limit: int = 20
# ) -> FollowsPublic:
#     """Get followers for a specific user."""
#     return follow_service.get_followers(user_id, skip, limit)


# @router.get("/following/{user_id}", response_model=FollowsPublic)
# def get_user_following(
#     user_id: uuid.UUID,
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser,
#     skip: int = 0,
#     limit: int = 20
# ) -> FollowsPublic:
#     """Get users that a specific user is following."""
#     return follow_service.get_following(user_id, skip, limit)



# @router.get("/stats", response_model=FollowStats)
# def get_my_follow_stats(
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser
# ) -> FollowStats:
#     """Get current user's follow statistics."""
#     return follow_service.get_follow_stats(current_user.id)


# @router.get("/stats/{user_id}", response_model=FollowStats)
# def get_user_follow_stats(
#     user_id: uuid.UUID,
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser
# ) -> FollowStats:
#     """Get follow statistics for a specific user."""
#     return follow_service.get_follow_stats(user_id)




# @router.get("/mutual", response_model=FollowsPublic)
# def get_mutual_follows(
#     follow_service: FollowServiceDep,
#     current_user: CurrentUser,
#     skip: int = 0,
#     limit: int = 20
# ) -> FollowsPublic:
#     """Get mutual follows (users who follow each other)."""
#     return follow_service.get_mutual_follows(current_user.id, skip, limit)
