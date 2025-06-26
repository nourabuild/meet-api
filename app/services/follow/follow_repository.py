import uuid

from sqlmodel import Session, and_, func, select

from app.utils.models import Follow, User


class FollowRepository:
    def __init__(self, session: Session):
        self.session = session

    def follow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> Follow:
        """Create a follow relationship."""
        # Check if already following
        existing = self.session.exec(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id
                )
            )
        ).first()

        if existing:
            raise ValueError("Already following this user")

        # Check if trying to follow self
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")

        # Create new follow relationship
        follow = Follow(follower_id=follower_id, following_id=following_id)
        self.session.add(follow)
        self.session.commit()
        self.session.refresh(follow)
        return follow

    def unfollow_user(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        """Remove a follow relationship."""
        follow = self.session.exec(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id
                )
            )
        ).first()

        if not follow:
            return False

        self.session.delete(follow)
        self.session.commit()
        return True

    def is_following(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        """Check if user is following another user."""
        follow = self.session.exec(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id
                )
            )
        ).first()
        return follow is not None
    
    def get_followers_with_users(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        followers = self.session.exec(
            select(Follow, User)
            .join(User, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return list(followers)


    def get_followers(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Follow]:
        """Get users who follow this user."""
        follows = self.session.exec(
            select(Follow)
            .where(Follow.following_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return list(follows)
    
    def get_following_with_users(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        following = self.session.exec(
            select(Follow, User)
            .join(User, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return list(following)

    def get_following(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Follow]:
        """Get users this user is following."""
        follows = self.session.exec(
            select(Follow).where(Follow.follower_id == user_id).offset(skip).limit(limit)
        ).all()
        return list(follows)

    def get_follow_stats(self, user_id: uuid.UUID) -> dict:
        """Get follower and following counts for a user."""
        followers_count = self.session.exec(
            select(func.count(Follow.id))
            .where(Follow.following_id == user_id)
        ).first() or 0

        following_count = self.session.exec(
            select(func.count(Follow.id))
            .where(Follow.follower_id == user_id)
        ).first() or 0

        return {
            "followers_count": followers_count,
            "following_count": following_count
        }

    def get_follow_status(self, user_id: uuid.UUID, target_user_id: uuid.UUID) -> dict:
        """Get follow relationship status between two users."""
        is_following = self.is_following(user_id, target_user_id)
        is_followed_by = self.is_following(target_user_id, user_id)

        return {
            "is_following": is_following,
            "is_followed_by": is_followed_by
        }

    def get_mutual_follows(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Follow]:
        """Get mutual follows (users who follow each other)."""
        # This is a more complex query - users who this user follows AND who follow back
        mutual_follows = self.session.exec(
            select(Follow)
            .where(Follow.follower_id == user_id)
            .where(
                Follow.following_id.in_(
                    select(Follow.follower_id)
                    .where(Follow.following_id == user_id)
                )
            )
            .offset(skip)
            .limit(limit)
        ).all()
        return list(mutual_follows)

    def count_followers(self, user_id: uuid.UUID) -> int:
        """Count total followers for a user."""
        count = self.session.exec(
            select(func.count(Follow.id))
            .where(Follow.following_id == user_id)
        ).first()
        return count or 0

    def count_following(self, user_id: uuid.UUID) -> int:
        """Count total users this user is following."""
        count = self.session.exec(
            select(func.count(Follow.id))
            .where(Follow.follower_id == user_id)
        ).first()
        return count or 0
