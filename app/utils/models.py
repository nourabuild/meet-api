"""SQLModel Schema Organization
==========================
This module contains all database models, schemas, and related types
organized by functional area for better maintainability.
"""

import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import Annotated

import phonenumbers
from pydantic import BeforeValidator, EmailStr
from sqlmodel import Field, Relationship, SQLModel

# ============================================================
# VALIDATORS & CUSTOM TYPES
# ============================================================


def lowercase_str(v: str | None) -> str | None:
    """Convert string to lowercase and strip whitespace."""
    if isinstance(v, str):
        return v.lower().strip()
    return v


def e164_phone(v: str | None) -> str | None:
    """Validate and format phone number to E164 format."""
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

        e164_number = phonenumbers.format_number(
            phone_number, phonenumbers.PhoneNumberFormat.E164
        )

        return e164_number
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"Invalid phone number format: {e}")
    except Exception as e:
        raise ValueError(f"Phone number validation error: {e}")


# Custom type annotations
LowercaseStr = Annotated[str, BeforeValidator(lowercase_str)]
LowercaseEmailStr = Annotated[EmailStr, BeforeValidator(lowercase_str)]
E164PhoneStr = Annotated[str, BeforeValidator(e164_phone)]


# ============================================================
# ENUMS
# ============================================================


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class MeetingStatus(str, Enum):
    """Meeting status enumeration."""

    NEW = "new"
    APPROVED = "approved"
    CANCELED = "canceled"


class ParticipantStatus(str, Enum):
    """Participant status enumeration."""

    NEW = "new"
    ACCEPTED = "accepted"
    DECLINED = "declined"


# ============================================================
# PHOTO MODULE
# ============================================================


class PhotoBase(SQLModel):
    """Base photo model with common fields."""

    small_uri: str | None = Field(default=None, max_length=500)
    medium_uri: str | None = Field(default=None, max_length=500)
    large_uri: str | None = Field(default=None, max_length=500)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Photo(PhotoBase, table=True):
    """Photo table model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


# ============================================================
# USER MODULE
# ============================================================


class UserBase(SQLModel):
    """Base user model with common fields."""

    name: str = Field(min_length=8, max_length=40)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    account: str = Field(unique=True, max_length=32)
    roles: UserRole = Field(default=UserRole.USER)

    is_active: bool = True
    is_verified: bool = True
    is_superuser: bool = False

    bio: str | None = Field(default=None, max_length=200)
    dob: date | None = Field(default=None)
    phone: E164PhoneStr | None = Field(default=None, max_length=20)

    avatar_photo_id: uuid.UUID | None = Field(default=None, foreign_key="photo.id")

    deleted_at: date | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class User(UserBase, table=True):
    """User table model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password_hash: str
    avatar_photo: Photo | None = Relationship(back_populates=None)


# User Schemas
class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    """Schema for user registration."""

    name: str = Field(min_length=8, max_length=40)
    email: LowercaseEmailStr = Field(max_length=255)
    account: LowercaseStr = Field(min_length=6, max_length=32)
    bio: str | None = Field(default=None, max_length=1000)
    dob: date | None = Field(default=None)
    phone: E164PhoneStr | None = Field(default=None, max_length=20)
    password: LowercaseStr = Field(min_length=8, max_length=40)


class UserUpdate(UserBase):
    """Schema for updating user information."""

    email: LowercaseEmailStr = Field(default=None, max_length=255)  # type: ignore
    account: LowercaseStr = Field(default=None, min_length=6, max_length=32)  # type: ignore
    password: LowercaseStr = Field(default=None, min_length=8, max_length=40)


class UpdatePassword(SQLModel):
    """Schema for updating user password."""

    current_password: LowercaseStr = Field(min_length=8, max_length=40)
    new_password: LowercaseStr = Field(min_length=8, max_length=40)


class UserPublic(UserBase):
    """Public user schema (excludes sensitive information)."""

    id: uuid.UUID


class UsersPublic(SQLModel):
    """Schema for paginated user list."""

    data: list[UserPublic]
    count: int


# ============================================================
# FOLLOW MODULE
# ============================================================


class FollowBase(SQLModel):
    """Base follow model with common fields."""

    follower_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    following_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Follow(FollowBase, table=True):
    """Follow table model for user relationships."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


# Follow Schemas
class FollowStatus(SQLModel):
    """Schema for follow relationship status."""

    is_following: bool
    is_followed_by: bool
    is_mutual: bool = Field(default=False)


class FollowingRelation(SQLModel):
    """Schema for following relationship details."""

    id: uuid.UUID
    following_id: uuid.UUID
    user: UserPublic
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FollowingListPublic(SQLModel):
    """Schema for paginated following list."""

    data: list[FollowingRelation]
    count: int


class FollowerRelation(SQLModel):
    """Schema for follower relationship details."""

    id: uuid.UUID
    follower_id: uuid.UUID
    user: UserPublic
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FollowerListPublic(SQLModel):
    """Schema for paginated follower list."""

    data: list[FollowerRelation]
    count: int


class FollowCountStatus(SQLModel):
    """Schema for follow count statistics."""

    following_count: int
    followers_count: int


# ============================================================
# MEETING TYPE MODULE
# ============================================================


class MeetingTypeBase(SQLModel):
    """Base meeting type model with common fields."""

    title: str = Field(min_length=10, max_length=30, unique=True, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MeetingType(MeetingTypeBase, table=True):
    """Meeting type table model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


# Meeting Type Schemas
class MeetingTypePublic(MeetingTypeBase):
    """Public meeting type schema."""

    id: uuid.UUID


# ============================================================
# MEETING MODULE
# ============================================================


class MeetingBase(SQLModel):
    """Base meeting model with common fields."""

    title: str = Field(min_length=6, max_length=40)

    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    owner_id: uuid.UUID = Field(foreign_key="user.id")

    type_id: uuid.UUID = Field(foreign_key="meetingtype.id")
    status: MeetingStatus = Field(default=MeetingStatus.NEW)

    start_time: datetime

    location: str = Field(min_length=6, max_length=40)
    location_url: str | None = Field(default=None, max_length=100)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Meeting(MeetingBase, table=True):
    """Meeting table model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Relationships
    participants: list["Participant"] = Relationship(back_populates="meeting")
    meeting_type: MeetingType = Relationship()
    owner: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Meeting.owner_id]"}
    )
    appointed_by_user: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Meeting.appointed_by]"}
    )
    assigned_to_user: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Meeting.assigned_to]"}
    )


# Meeting Schemas
class MeetingObject(SQLModel):
    """Schema for meeting object in creation."""

    title: str = Field(min_length=6, max_length=40)
    appointed_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_to: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    type: str = Field(min_length=1, max_length=50)  # Accept type as string
    status: MeetingStatus = Field(default=MeetingStatus.NEW)
    start_time: datetime
    location: str = Field(min_length=6, max_length=40)
    location_url: str | None = Field(default=None, max_length=100)


class MeetingCreate(SQLModel):
    """Schema for creating a new meeting with participants."""

    meeting: MeetingObject
    participants: list["ParticipantObject"] = []


class MeetingPublic(MeetingBase):
    """Public meeting schema with participants."""

    id: uuid.UUID
    meeting_type: MeetingTypePublic
    participants: list["ParticipantPublic"] = []


# ============================================================
# PARTICIPANT MODULE
# ============================================================


class ParticipantBase(SQLModel):
    """Base participant model with common fields."""

    meeting_id: uuid.UUID = Field(foreign_key="meeting.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")

    status: ParticipantStatus = Field(default=ParticipantStatus.NEW)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Participant(ParticipantBase, table=True):
    """Participant table model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    meeting: Meeting = Relationship(back_populates="participants")
    user: User = Relationship()


# Participant Schemas
class ParticipantObject(SQLModel):
    """Schema for participant object in meeting creation."""

    user_id: uuid.UUID
    status: ParticipantStatus = Field(default=ParticipantStatus.NEW)


class ParticipantPublic(ParticipantBase):
    """Public participant schema with user information."""

    id: uuid.UUID
    user: UserPublic


# ============================================================
# AUTHENTICATION MODULE
# ============================================================


class Message(SQLModel):
    """Generic message schema."""

    message: str


class Token(SQLModel):
    """JSON payload containing access token."""

    access_token: str
    token_type: str = "bearer"


class TokenWithRefresh(SQLModel):
    """JSON payload containing both access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(SQLModel):
    """Refresh token request schema."""

    refresh_token: str


class TokenPayload(SQLModel):
    """Contents of JWT token."""

    sub: str | None = None


class NewPassword(SQLModel):
    """Schema for password reset."""

    token: str
    new_password: str = Field(min_length=8, max_length=40)


class EmailPasswordLogin(SQLModel):
    """Schema for email/password login."""

    email: str
    password: str


# ============================================================
# FORWARD REFERENCES
# ============================================================

# Update forward references for proper type resolution
# MeetingCreate.model_rebuild()
# MeetingPublic.model_rebuild()
# ParticipantPublic.model_rebuild()
