import uuid

from app.services.follow.follow_repository import FollowRepository
from app.utils.models import FollowerListPublic, FollowingListPublic, FollowStatus


class FollowService:
    def __init__(self, follow_repository: FollowRepository):
        self.follow_repository = follow_repository

    # def follow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> FollowPublic:
    #     """Follow a user."""
    #     follow = self.follow_repository.follow_user(follower_id, following_id)
    #     return FollowPublic(
    #         id=follow.id,
    #         follower_id=follow.follower_id,
    #         following_id=follow.following_id,
    #         created_at=follow.created_at
    #     )

    def unfollow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        """Unfollow a user."""
        return self.follow_repository.unfollow_user(follower_id, following_id)

    def follow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        """Follow a user."""
        return self.follow_repository.follow_user(follower_id, following_id)

    def get_following_list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[FollowingListPublic]:
        # repository returns Follow objects with .following loaded (relationship)
        return self.follow_repository.get_following(user_id, skip, limit)

    def get_followers_list(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[FollowerListPublic]:
        # repository returns Follow objects with .follower loaded (relationship)
        return self.follow_repository.get_followers(user_id, skip, limit)


    def get_follow_status(self, user_id: uuid.UUID, target_user_id: uuid.UUID) -> FollowStatus:
        """Get follow relationship status between two users."""
        return self.follow_repository.get_follow_status(user_id, target_user_id)
