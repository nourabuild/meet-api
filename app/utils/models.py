import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import Annotated, List

import phonenumbers
from pydantic import BeforeValidator, EmailStr
from sqlmodel import Field, Relationship, SQLModel


def lowercase_str(v: str | None) -> str | None:
    if isinstance(v, str):
        return v.lower().strip()
    return v


def e164_phone(v: str | None) -> str | None:
    if v is None:
        return v

    if not isinstance(v, str):
        raise ValueError("Phone number must be a string")

    v = v.strip()

    if not v:
        return None

    try:
        phone_number = phonenumbers.parse(v, None)

        if not phonenumbers.is_valid_number(phone_number):
            raise ValueError("Invalid phone number")

        e164_number = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)

        return e164_number
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"Invalid phone number format: {e}")
    except Exception as e:
        raise ValueError(f"Phone number validation error: {e}")

LowercaseStr = Annotated[str, BeforeValidator(lowercase_str)]
LowercaseEmailStr = Annotated[EmailStr, BeforeValidator(lowercase_str)]
E164PhoneStr = Annotated[str, BeforeValidator(e164_phone)]

# ------------------------------------------------------------
# Enums
# ------------------------------------------------------------

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class MeetingType(str, Enum):
    ALL_HANDS = "all-hands"
    ONE_ON_ONE = "one-on-one"
    TEAM_MEETING = "team-meeting"
    STANDUP = "standup"
    PROJECT_MEETING = "project-meeting"


class MeetingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ParticipantStatus(str, Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    DECLINED = "declined"

# ------------------------------------------------------------
# Base 
# ------------------------------------------------------------

class UserBase(SQLModel):
    name: str = Field(min_length=8, max_length=40)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    account: str = Field(unique=True, max_length=32)
    roles: UserRole = Field(default=UserRole.USER)

    is_active: bool = True # n
    is_verified: bool = True # n
    is_superuser: bool = False # n

    bio: str | None = Field(default=None, max_length=200)
    dob: date | None = Field(default=None)
    phone: E164PhoneStr | None = Field(default=None, max_length=20)

    avatar_photo_id: uuid.UUID | None = Field(default=None, foreign_key="photo.id")

    deleted_at: date | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PhotoBase(SQLModel):
    small_uri: str | None = Field(default=None, max_length=500)
    medium_uri: str | None = Field(default=None, max_length=500)
    large_uri: str | None = Field(default=None, max_length=500)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class FollowBase(SQLModel):
    follower_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    following_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Optionally, you can add relationships if you want to access user objects directly
    # follower: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "[Follow.follower_id]"})
    # following: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "[Follow.following_id]"})


class MeetingBase(SQLModel):
    title: str = Field(min_length=6, max_length=40)
    
    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    
    type: MeetingType = Field(default=MeetingType.ALL_HANDS)
    status: MeetingStatus = Field(default=MeetingStatus.PENDING)

    start_time: datetime
    
    location: str = Field(min_length=6, max_length=40)
    location_url: str | None = Field(default=None, max_length=100)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ParticipantBase(SQLModel):
    meeting_id: uuid.UUID = Field(foreign_key="meeting.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    
    status: ParticipantStatus = Field(default=ParticipantStatus.NEW)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

# ------------------------------------------------------------
# Tables
# ------------------------------------------------------------

class Photo(PhotoBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password_hash: str
    avatar_photo: Photo | None = Relationship(back_populates=None)


class Follow(FollowBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class Meeting(MeetingBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Relationships
    participants: List["Participant"] = Relationship(back_populates="meeting")
    owner: User = Relationship(sa_relationship_kwargs={"foreign_keys": "[Meeting.owner_id]"})
    appointed_by_user: User | None = Relationship(sa_relationship_kwargs={"foreign_keys": "[Meeting.appointed_by]"})
    assigned_to_user: User | None = Relationship(sa_relationship_kwargs={"foreign_keys": "[Meeting.assigned_to]"})


class Participant(ParticipantBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    meeting: Meeting = Relationship(back_populates="participants")
    user: User = Relationship()

# ------------------------------------------------------------
# User
# ------------------------------------------------------------

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)

class UserRegister(SQLModel):
    name: str = Field(min_length=8, max_length=40)
    email: LowercaseEmailStr = Field(max_length=255)
    account: LowercaseStr = Field(min_length=6, max_length=32)
    bio: str | None = Field(default=None, max_length=1000)
    dob: date | None = Field(default=None)
    phone: E164PhoneStr | None = Field(default=None, max_length=20)
    password: LowercaseStr = Field(min_length=8, max_length=40)

# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: LowercaseEmailStr = Field(default=None, max_length=255)  # type: ignore
    account: LowercaseStr = Field(default=None, min_length=6, max_length=32)  # type: ignore
    password: LowercaseStr = Field(default=None, min_length=8, max_length=40)

class UpdatePassword(SQLModel):
    current_password: LowercaseStr = Field(min_length=8, max_length=40)
    new_password: LowercaseStr = Field(min_length=8, max_length=40)

class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# JSON payload containing both access and refresh tokens
class TokenWithRefresh(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Refresh token request
class RefreshTokenRequest(SQLModel):
    refresh_token: str


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

class EmailPasswordLogin(SQLModel):
    email: str
    password: str

# ------------------------------------------------------------
# Follow
# ------------------------------------------------------------

class FollowStatus(SQLModel):
    is_following: bool
    is_followed_by: bool
    is_mutual: bool = Field(default=False)


class FollowingRelation(SQLModel):
    id: uuid.UUID
    following_id: uuid.UUID
    user: UserPublic
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FollowingListPublic(SQLModel):
    data: List[FollowingRelation]
    count: int


class FollowerRelation(SQLModel):
    id: uuid.UUID
    follower_id: uuid.UUID
    user: UserPublic
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FollowerListPublic(SQLModel):
    data: List[FollowerRelation]
    count: int

# ------------------------------------------------------------
# Meeting
# ------------------------------------------------------------

class MeetingObject(SQLModel):
    title: str = Field(min_length=6, max_length=40)
    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    type: MeetingType = Field(default=MeetingType.ALL_HANDS)
    status: MeetingStatus = Field(default=MeetingStatus.PENDING)
    start_time: datetime
    location: str = Field(min_length=6, max_length=40)
    location_url: str | None = Field(default=None, max_length=100)

class ParticipantObject(SQLModel):
    user_id: uuid.UUID
    status: ParticipantStatus = Field(default=ParticipantStatus.NEW)

class MeetingCreate(SQLModel):
    meeting: MeetingObject
    participants: List[ParticipantObject] = []


class ParticipantPublic(ParticipantBase):
    id: uuid.UUID
    user: UserPublic


class MeetingPublic(MeetingBase):
    id: uuid.UUID
    participants: List[ParticipantPublic] = []