"""
Follow Service
==============
Handles business logic for user follow/unfollow actions,
follower/following list retrieval, and relationship status checks.
"""

import uuid

from app.services.follow.follow_repository import FollowRepository
from app.utils.models import FollowerListPublic, FollowingListPublic, FollowStatus


class FollowService:
    def __init__(self, follow_repository: FollowRepository):
        self.follow_repository = follow_repository

    def unfollow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        return self.follow_repository.unfollow_user(follower_id, following_id)

    def follow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        return self.follow_repository.follow_user(follower_id, following_id)

    def get_following_list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[FollowingListPublic]:
        return self.follow_repository.get_following(user_id, skip, limit)

    def get_followers_list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[FollowerListPublic]:
        return self.follow_repository.get_followers(user_id, skip, limit)

    def get_follow_status(self, user_id: uuid.UUID, target_user_id: uuid.UUID) -> FollowStatus:
        return self.follow_repository.get_follow_status(user_id, target_user_id)
