import uuid

from app.services.follow.follow_repository import FollowRepository
from app.utils.models import (
    FollowPublic,
    FollowWithUserPublic,
    FollowerWithUserList,
    FollowingWithUserList,
    FollowsPublic,
    FollowStats,
    FollowStatus,
    UserPublic,
)


class FollowService:
    def __init__(self, follow_repository: FollowRepository):
        self.follow_repository = follow_repository

    def follow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> FollowPublic:
        """Follow a user."""
        follow = self.follow_repository.follow_user(follower_id, following_id)
        return FollowPublic(
            id=follow.id,
            follower_id=follow.follower_id,
            following_id=follow.following_id,
            created_at=follow.created_at
        )

    def unfollow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        """Unfollow a user."""
        return self.follow_repository.unfollow_user(follower_id, following_id)

    def get_followers(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> FollowsPublic:
        """Get followers for a user."""
        follows = self.follow_repository.get_followers(user_id, skip, limit)
        total_count = self.follow_repository.count_followers(user_id)

        follow_data = [
            FollowPublic(
                id=follow.id,
                follower_id=follow.follower_id,
                following_id=follow.following_id,
                created_at=follow.created_at
            )
            for follow in follows
        ]

        return FollowsPublic(data=follow_data, count=total_count)
    
    def get_followers_with_users(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[FollowerWithUserList]:
        return self.follow_repository.get_followers_with_users(user_id, skip, limit)

    def get_following(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> FollowsPublic:
        """Get users this user is following."""
        follows = self.follow_repository.get_following(user_id, skip, limit)
        total_count = self.follow_repository.count_following(user_id)

        follow_data = [
            FollowPublic(
                id=follow.id,
                follower_id=follow.follower_id,
                following_id=follow.following_id,
                created_at=follow.created_at
            )
            for follow in follows
        ]

        return FollowsPublic(data=follow_data, count=total_count)
    
    def get_following_with_users(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[FollowingWithUserList]:
        # repository returns Follow objects with .following loaded (relationship)
        return self.follow_repository.get_following_with_users(user_id, skip, limit)

    def get_follow_stats(self, user_id: uuid.UUID) -> FollowStats:
        """Get follow statistics for a user."""
        stats = self.follow_repository.get_follow_stats(user_id)
        return FollowStats(
            followers_count=stats["followers_count"],
            following_count=stats["following_count"]
        )

    def get_follow_status(self, user_id: uuid.UUID, target_user_id: uuid.UUID) -> FollowStatus:
        """Get follow relationship status between two users."""
        status = self.follow_repository.get_follow_status(user_id, target_user_id)
        return FollowStatus(
            is_following=status["is_following"],
            is_followed_by=status["is_followed_by"]
        )

    def get_mutual_follows(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> FollowsPublic:
        """Get mutual follows."""
        follows = self.follow_repository.get_mutual_follows(user_id, skip, limit)
        # For count, we need to count all mutual follows, not just the paginated results
        total_count = len(self.follow_repository.get_mutual_follows(user_id, 0, 1000))  # Get all for count

        follow_data = [
            FollowPublic(
                id=follow.id,
                follower_id=follow.follower_id,
                following_id=follow.following_id,
                created_at=follow.created_at
            )
            for follow in follows
        ]

        return FollowsPublic(data=follow_data, count=total_count)

    def is_following(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        """Check if user is following another user."""
        return self.follow_repository.is_following(follower_id, following_id)
