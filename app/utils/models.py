import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import Annotated

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
    CLIENT_MEETING = "client-meeting"
    STANDUP = "standup"
    RETROSPECTIVE = "retrospective"

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
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    # Optionally, you can add relationships if you want to access user objects directly
    # follower: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "[Follow.follower_id]"})
    # following: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "[Follow.following_id]"})


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
    data: list[UserPublic]
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
    data: list[FollowingRelation]
    count: int


class FollowerRelation(SQLModel):
    id: uuid.UUID
    follower_id: uuid.UUID
    user: UserPublic
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FollowerListPublic(SQLModel):
    data: list[FollowerRelation]
    count: int

# ------------------------------------------------------------
# Meeting
# ------------------------------------------------------------

# Base models for meetings
class MeetingBase(SQLModel):
    title: str = Field(max_length=255)
    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    type: MeetingType = Field(default=MeetingType.ALL_HANDS)
    status: MeetingStatus = Field(default=MeetingStatus.PENDING)
    start_time: datetime
    location: str = Field(max_length=255)
    location_url: str | None = Field(default=None, max_length=500)

# Base model for meeting creation (without owner_id)
class MeetingCreateBase(SQLModel):
    title: str = Field(max_length=255)
    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    type: MeetingType = Field(default=MeetingType.ALL_HANDS)
    status: MeetingStatus = Field(default=MeetingStatus.PENDING)
    start_time: datetime
    location: str = Field(max_length=255)
    location_url: str | None = Field(default=None, max_length=500)

class MeetingCreate(MeetingCreateBase):
    pass

class MeetingUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255)
    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    type: MeetingType | None = Field(default=None)
    status: MeetingStatus | None = Field(default=None)
    start_time: datetime | None = Field(default=None)
    location: str | None = Field(default=None, max_length=255)
    location_url: str | None = Field(default=None, max_length=500)

# Database models
class Meeting(MeetingBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    participants: list["Participant"] = Relationship(back_populates="meeting")
    owner: User = Relationship(sa_relationship_kwargs={"foreign_keys": "[Meeting.owner_id]"})
    appointed_by_user: User | None = Relationship(sa_relationship_kwargs={"foreign_keys": "[Meeting.appointed_by]"})
    assigned_to_user: User | None = Relationship(sa_relationship_kwargs={"foreign_keys": "[Meeting.assigned_to]"})

class Participant(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    meeting_id: uuid.UUID = Field(foreign_key="meeting.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    status: ParticipantStatus = Field(default=ParticipantStatus.NEW)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    meeting: Meeting = Relationship(back_populates="participants")
    user: User = Relationship()

# API response models with relationships
class ParticipantPublic(SQLModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    user_id: uuid.UUID
    status: ParticipantStatus
    created_at: datetime
    updated_at: datetime
    user: UserPublic

class MeetingPublic(MeetingBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    participants: list[ParticipantPublic] = []
    owner_id: uuid.UUID
    appointed_by: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None

class MeetingsPublic(SQLModel):
    data: list[MeetingPublic]
    count: int

# Participant management models
class ParticipantCreate(SQLModel):
    user_id: uuid.UUID
    status: ParticipantStatus = Field(default=ParticipantStatus.NEW)

class ParticipantUpdate(SQLModel):
    status: ParticipantStatus

class ParticipantBulkCreate(SQLModel):
    participants: list[ParticipantCreate]

# Meeting with participant IDs only (for efficient queries)
class MeetingWithParticipantIds(MeetingBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    participant_ids: list[uuid.UUID] = []

# Model for creating meetings with participants in one transaction
class MeetingWithParticipantsCreate(SQLModel):
    meeting: MeetingCreate
    participants: list[ParticipantCreate] = []

# Meeting Request models for pending invitations
class MeetingRequestPublic(SQLModel):
    """Public model for meeting requests (pending invitations)"""
    id: uuid.UUID
    meeting_id: uuid.UUID
    user_id: uuid.UUID
    status: ParticipantStatus
    created_at: datetime
    updated_at: datetime
    meeting: MeetingPublic
    user: UserPublic

class MeetingRequestsPublic(SQLModel):
    """List of meeting requests with count"""
    data: list[MeetingRequestPublic]
    count: int





# class Photo(SQLModel, table=True):
#     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

#     small_uri: str | None = Field(default=None, max_length=500)
#     medium_uri: str | None = Field(default=None, max_length=500)
#     large_uri: str | None = Field(default=None, max_length=500)

#     created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
#     updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
