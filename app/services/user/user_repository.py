import uuid

from sqlmodel import Session, col, delete, func, select, update

from app.utils.config import settings
from app.utils.models import User, UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password


class UserRepository:

    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_create: UserCreate) -> User:
        db_obj = User.model_validate(
            user_create, update={"password_hash": get_password_hash(user_create.password)}
        )
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        statement = self.session.get(
            User, user_id
        )
        return statement
        
    def get_user_by_email(self, email: str) -> User | None:
        statement = self.session.exec(
            select(User).where(User.email == email)
        ).first()
        return statement

    def get_user_by_account(self, account: str) -> User | None:
        statement = self.session.exec(
            select(User).where(User.account == account)
        ).first()
        return statement
        
    def get_users(self, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        count_statement = select(func.count()).select_from(User)
        count = self.session.exec(count_statement).one()

        statement = select(User).offset(skip).limit(limit)
        users = self.session.exec(statement).all()

        return users, count

    def update_user(self, db_user: User, user_in: UserUpdate) -> User:
        user_data = user_in.model_dump(exclude_unset=True)
        extra_data = {}
        if "password" in user_data:
            password = user_data["password"]
            password_hash = get_password_hash(password)
            extra_data["password_hash"] = password_hash
            del user_data["password"]

        db_user.sqlmodel_update(user_data, update=extra_data)
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def update_user_password(self, db_user: User, password_hash: str) -> User:
        db_user.password_hash = password_hash
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def delete_user(self, user_id: uuid.UUID) -> bool:
        statement = delete(User).where(col(User.id) == user_id)
        result = self.session.exec(statement)
        self.session.commit()
        return result.rowcount > 0

    def authenticate(self, email: str, password: str) -> User | None:
        db_user = self.get_user_by_email(email)
        if not db_user:
            return None
        if not verify_password(password, db_user.password_hash):
            return None
        return db_user

    def is_email_taken(self, email: str, exclude_user_id: uuid.UUID | None = None) -> bool:
        statement = select(User).where(User.email == email)
        if exclude_user_id:
            statement = statement.where(User.id != exclude_user_id)
        return self.session.exec(statement).first() is not None

    def is_account_taken(self, account: str, exclude_user_id: uuid.UUID | None = None) -> bool:
        statement = select(User).where(User.account == account)
        if exclude_user_id:
            statement = statement.where(User.id != exclude_user_id)
        return self.session.exec(statement).first() is not None

    def search_users(self, query: str, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        # Search by name, account, or email (case-insensitive)
        search_filter = (
            (User.name.ilike(f"%{query}%")) |
            (User.account.ilike(f"%{query}%")) |
            (User.email.ilike(f"%{query}%"))
        )

        count_statement = select(func.count()).select_from(User).where(search_filter)
        count = self.session.exec(count_statement).one()

        statement = select(User).where(search_filter).offset(skip).limit(limit)
        users = self.session.exec(statement).all()

        return users, count

    def soft_delete_user(self, user_id: uuid.UUID) -> bool:
        from datetime import date, timedelta

        user = self.get_user_by_id(user_id)
        if not user:
            return False

        # Schedule deletion for grace period using explicit update
        deletion_date = date.today() + timedelta(days=settings.USER_DELETION_GRACE_PERIOD_DAYS)

        # Use SQL update to ensure no field conflicts
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(deletion_scheduled_at=deletion_date, is_active=True)
        )
        self.session.exec(stmt)
        self.session.commit()
        return True

    def recover_user(self, user_id: uuid.UUID) -> bool:
        user = self.get_user_by_id(user_id)
        if not user or user.deletion_scheduled_at is None:
            return False

        # Check if still within recovery period
        from datetime import date
        if date.today() > user.deletion_scheduled_at:
            return False  # Too late to recover

        # Recover the user using explicit SQL update
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(deletion_scheduled_at=None, is_active=True)
        )
        self.session.exec(stmt)
        self.session.commit()
        return True

    def get_user_deletion_info(self, user_id: uuid.UUID) -> dict:
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User not found for ID: {user_id}")

        if user.deletion_scheduled_at is None:
            return {"is_scheduled_for_deletion": False}

        from datetime import date
        days_left = (user.deletion_scheduled_at - date.today()).days
        return {
            "is_scheduled_for_deletion": True,
            "deletion_scheduled_at": user.deletion_scheduled_at,
            "days_until_permanent_deletion": days_left,
            "can_recover": days_left > 0
        }
