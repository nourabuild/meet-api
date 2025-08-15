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

    # Relationships


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
    
    __tablename__ = "meeting_type"
    
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

    type_id: uuid.UUID = Field(foreign_key="meeting_type.id")
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
# CALENDAR MODULE
# ============================================================


class GoogleCalendarAuth(SQLModel, table=True):
    """Google Calendar OAuth authentication table."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True)
    access_token: str
    refresh_token: str
    expires_at: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates=None)


class Calendar(SQLModel, table=True):
    """User calendar availability table."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    day_of_week: int = Field(ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str  # Time format like "09:00"
    end_time: str    # Time format like "17:00"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates=None)


class AvailabilityException(SQLModel, table=True):
    """Exceptions to regular calendar availability with recurrence support."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    exception_date: date
    recurrence_type: str | None = None  # "weekly", "monthly", etc.
    day_of_week: int | None = Field(None, ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str | None = None  # If None, unavailable all day
    end_time: str | None = None    # If None, unavailable all day
    is_available: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates=None)


class Onboarding(SQLModel, table=True):
    """User onboarding progress tracking."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True)
    calendar: bool = Field(default=False)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates=None)


class CalendarEvent(SQLModel, table=True):
    """Calendar events synced from Google Calendar."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    google_event_id: str = Field(unique=True)
    title: str
    start_time: str
    end_time: str
    calendar_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates=None)


class CalendarAuthResponse(SQLModel):
    """Response schema for calendar authentication status."""

    is_connected: bool
    oauth_url: str | None = None


class CalendarAvailabilityPublic(SQLModel):
    """Public schema for calendar availability."""

    id: uuid.UUID
    day_of_week: int
    start_time: str
    end_time: str


class CalendarAvailabilityCreate(SQLModel):
    """Schema for creating calendar availability."""

    day_of_week: int = Field(ge=0, le=6)
    start_time: str
    end_time: str


class CalendarAvailabilityUpdate(SQLModel):
    """Schema for updating calendar availability."""

    start_time: str | None = None
    end_time: str | None = None


class AvailabilityExceptionPublic(SQLModel):
    """Public schema for availability exceptions."""

    id: uuid.UUID
    date: date
    start_time: str | None
    end_time: str | None
    is_available: bool


class TimeInterval(SQLModel):
    """Time interval schema."""
    
    start_time: str
    end_time: str


class CalendarIntervalCreate(SQLModel):
    """Schema for creating calendar intervals."""
    
    day_of_week: int = Field(ge=0, le=6)
    intervals: list[TimeInterval]


class AvailabilityExceptionCreate(SQLModel):
    """Schema for creating availability exceptions with recurrence."""

    exception_date: date
    recurrence_type: str | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: str | None = None
    end_time: str | None = None
    is_available: bool = Field(default=False)


class OnboardingPublic(SQLModel):
    """Public schema for onboarding status."""

    id: uuid.UUID
    calendar: bool
    completed: bool


class OnboardingUpdate(SQLModel):
    """Schema for updating onboarding status."""

    calendar: bool | None = None
    completed: bool | None = None


class CalendarEventPublic(SQLModel):
    """Public schema for calendar events."""

    id: uuid.UUID
    title: str
    start_time: str
    end_time: str
    calendar_id: str


class CalendarEventsResponse(SQLModel):
    """Response schema for calendar events list."""

    events: list[CalendarEventPublic]
    count: int


class CalendarAvailabilityResponse(SQLModel):
    """Response schema for calendar availability list."""

    availability: list[CalendarAvailabilityPublic]
    count: int


class AvailabilityExceptionsResponse(SQLModel):
    """Response schema for availability exceptions list."""

    exceptions: list[AvailabilityExceptionPublic]
    count: int


class CalendarEntriesResponse(SQLModel):
    """Response schema for calendar entries."""
    
    entries: list[CalendarAvailabilityPublic]
    count: int


class CalendarGroupedResponse(SQLModel):
    """Response schema for grouped calendar data."""
    
    grouped_by_day: dict[int, list[TimeInterval]]


class GoogleCalendarAuthUrl(SQLModel):
    """Schema for Google Calendar auth URL."""
    
    auth_url: str


class GoogleCalendarConnect(SQLModel):
    """Schema for Google Calendar OAuth callback."""
    
    code: str
    state: str
    client_id: str
    redirect_uri: str


class GoogleCalendarFreeBusy(SQLModel):
    """Schema for Google Calendar freebusy request."""
    
    start_datetime: str
    end_datetime: str


class FreeBusyResponse(SQLModel):
    """Response schema for freebusy data."""
    
    busy_times: list[TimeInterval]
    free_times: list[TimeInterval]


# ============================================================
# FORWARD REFERENCES
# ============================================================

# Update forward references for proper type resolution
# MeetingCreate.model_rebuild()
# MeetingPublic.model_rebuild()
# ParticipantPublic.model_rebuild()
