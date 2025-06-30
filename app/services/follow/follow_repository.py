from typing import List
import uuid

from sqlmodel import Session, and_, or_, select

from app.utils.models import Follow, FollowStatus, User


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
    

    def get_following(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        following = self.session.exec(
            select(Follow, User)
            .join(User, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return List(following)
    
    
    def get_followers(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        followers = self.session.exec(
            select(Follow, User)
            .join(User, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .offset(skip)
            .limit(limit)
        ).all()
        return List(followers)


    def get_follow_status(self, user_id: uuid.UUID, target_user_id: uuid.UUID) -> FollowStatus:
        """Get follow relationship status between two users with a single optimized query."""
        # Edge case: same user
        if user_id == target_user_id:
            return FollowStatus(
                is_following=False, 
                is_followed_by=False, 
                is_mutual=False
            )
        
        # Single query to check both directions efficiently
        follows = self.session.exec(
            select(Follow.follower_id, Follow.following_id).where(
                or_(
                    and_(Follow.follower_id == user_id, Follow.following_id == target_user_id),
                    and_(Follow.follower_id == target_user_id, Follow.following_id == user_id)
                )
            )
        ).all()
        
        is_following = any(f.follower_id == user_id and f.following_id == target_user_id for f in follows)
        is_followed_by = any(f.follower_id == target_user_id and f.following_id == user_id for f in follows)
        
        return FollowStatus(
            is_following=is_following,
            is_followed_by=is_followed_by,
            is_mutual=is_following and is_followed_by
        )