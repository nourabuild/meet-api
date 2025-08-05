"""Follow Repository
=================
Manages database operations for following relationships,
including follow/unfollow actions, followers/following queries,
and mutual follow status checks.
"""

import uuid

from sqlmodel import Session, and_, func, or_, select

from app.utils.models import Follow, FollowStatus, User


class FollowRepository:
    def __init__(self, session: Session):
        self.session = session

    def follow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> Follow:
        existing = self.session.exec(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
        ).first()

        if existing:
            raise ValueError("Already following this user")

        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")

        follow = Follow(follower_id=follower_id, following_id=following_id)
        self.session.add(follow)
        self.session.commit()
        self.session.refresh(follow)
        return follow

    def unfollow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        follow = self.session.exec(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
        ).first()

        if not follow:
            return False

        self.session.delete(follow)
        self.session.commit()
        return True

    def get_following(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        following = self.session.exec(
            select(Follow, User)
            .join(User, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return list(following)

    def get_followers(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        followers = self.session.exec(
            select(Follow, User)
            .join(User, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return list(followers)

    def get_follow_status(
        self, user_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> FollowStatus:
        if user_id == target_user_id:
            return FollowStatus(
                is_following=False, is_followed_by=False, is_mutual=False
            )

        follows = self.session.exec(
            select(Follow.follower_id, Follow.following_id).where(
                or_(
                    and_(
                        Follow.follower_id == user_id,
                        Follow.following_id == target_user_id,
                    ),
                    and_(
                        Follow.follower_id == target_user_id,
                        Follow.following_id == user_id,
                    ),
                )
            )
        ).all()

        is_following = any(
            f.follower_id == user_id and f.following_id == target_user_id
            for f in follows
        )
        is_followed_by = any(
            f.follower_id == target_user_id and f.following_id == user_id
            for f in follows
        )

        return FollowStatus(
            is_following=is_following,
            is_followed_by=is_followed_by,
            is_mutual=is_following and is_followed_by,
        )

    def get_follow_counts(self, user_id: uuid.UUID) -> tuple[int, int]:
        """Get follower and following counts for a user.
        
        Returns:
            tuple[int, int]: (following_count, followers_count)
        """
        # Count how many users this user is following
        following_count = self.session.exec(
            select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        ).one()
        
        # Count how many users are following this user
        followers_count = self.session.exec(
            select(func.count(Follow.id)).where(Follow.following_id == user_id)
        ).one()
        
        return following_count, followers_count
