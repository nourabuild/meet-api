from sqlmodel import Session, create_engine

from app.services.user.user_repository import UserRepository
from app.utils.config import settings
from app.utils.models import UserCreate

# Use sync PostgreSQL URL for SQLModel
engine = create_engine(str(settings.SYNC_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28

def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    repository = UserRepository(session)
    user = repository.get_user_by_email(settings.FIRST_SUPERUSER)
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            account=settings.FIRST_SUPERUSER_ACCOUNT,
            is_superuser=True,
        )
        user = repository.create_user(user_in)
