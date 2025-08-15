"""Calendar Service
================
Business logic for Google Calendar integration including OAuth flow,
event synchronization, and calendar management operations.
"""

import uuid
from typing import Optional

from app.services.calendar.calendar_repository import CalendarRepository
from app.utils.config import settings
from app.utils.models import (
    GoogleCalendarAuth,
    CalendarEvent,
    Calendar,
    AvailabilityException,
    Onboarding,
)


class CalendarService:
    def __init__(self, calendar_repository: CalendarRepository) -> None:
        self.calendar_repository = calendar_repository

    def get_user_calendar_auth(self, user_id: uuid.UUID) -> Optional[GoogleCalendarAuth]:
        """Get user's Google Calendar authentication."""
        return self.calendar_repository.get_user_calendar_auth(user_id)

    def save_calendar_auth(
        self,
        user_id: uuid.UUID,
        access_token: str,
        refresh_token: str,
        expires_at: int,
    ) -> GoogleCalendarAuth:
        """Save or update Google Calendar authentication."""
        existing_auth = self.calendar_repository.get_user_calendar_auth(user_id)
        
        if existing_auth:
            return self.calendar_repository.update_calendar_auth(
                existing_auth, access_token, expires_at
            )
        else:
            return self.calendar_repository.create_calendar_auth(
                user_id, access_token, refresh_token, expires_at
            )

    def remove_calendar_auth(self, user_id: uuid.UUID) -> bool:
        """Remove Google Calendar authentication for a user."""
        return self.calendar_repository.delete_calendar_auth(user_id)

    def get_calendar_events(self, user_id: uuid.UUID) -> list[CalendarEvent]:
        """Get all calendar events for a user."""
        return self.calendar_repository.get_calendar_events(user_id)

    def sync_calendar_event(
        self,
        user_id: uuid.UUID,
        google_event_id: str,
        title: str,
        start_time: str,
        end_time: str,
        calendar_id: str,
    ) -> CalendarEvent:
        """Sync a calendar event from Google Calendar."""
        return self.calendar_repository.create_calendar_event(
            user_id, google_event_id, title, start_time, end_time, calendar_id
        )

    def get_oauth_url(self) -> str:
        """Generate Google Calendar OAuth URL."""
        from urllib.parse import urlencode
        
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
            "redirect_uri": f"{settings.FRONTEND_HOST}/calendar/callback",
            "scope": "https://www.googleapis.com/auth/calendar.readonly",
            "access_type": "offline",
            "prompt": "consent",
        }
        
        return f"{base_url}?{urlencode(params)}"

    def is_calendar_connected(self, user_id: uuid.UUID) -> bool:
        """Check if user has connected their Google Calendar."""
        auth = self.get_user_calendar_auth(user_id)
        return auth is not None

    # Calendar Availability Services
    def get_user_availability(self, user_id: uuid.UUID) -> list[Calendar]:
        """Get user's calendar availability."""
        return self.calendar_repository.get_user_availability(user_id)

    def create_availability(
        self,
        user_id: uuid.UUID,
        day_of_week: int,
        start_time: str,
        end_time: str,
    ) -> Calendar:
        """Create new availability for a user."""
        return self.calendar_repository.create_availability(
            user_id, day_of_week, start_time, end_time
        )

    def update_availability(
        self,
        availability_id: uuid.UUID,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> Optional[Calendar]:
        """Update existing availability."""
        return self.calendar_repository.update_availability(
            availability_id, start_time, end_time
        )

    def delete_availability(self, availability_id: uuid.UUID) -> bool:
        """Delete availability record."""
        return self.calendar_repository.delete_availability(availability_id)

    # Availability Exception Services
    def get_user_exceptions(self, user_id: uuid.UUID) -> list[AvailabilityException]:
        """Get user's availability exceptions."""
        return self.calendar_repository.get_user_exceptions(user_id)

    def create_exception(
        self,
        user_id: uuid.UUID,
        exception_date: str,
        recurrence_type: str | None = None,
        day_of_week: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        is_available: bool = False,
    ) -> AvailabilityException:
        """Create new availability exception with recurrence support."""
        return self.calendar_repository.create_exception(
            user_id, exception_date, recurrence_type, day_of_week, start_time, end_time, is_available
        )

    def delete_exception(self, exception_id: uuid.UUID) -> bool:
        """Delete availability exception."""
        return self.calendar_repository.delete_exception(exception_id)

    # Onboarding Services
    def get_user_onboarding(self, user_id: uuid.UUID) -> Optional[Onboarding]:
        """Get user's onboarding status."""
        return self.calendar_repository.get_user_onboarding(user_id)

    def update_onboarding(
        self,
        user_id: uuid.UUID,
        calendar: bool | None = None,
        completed: bool | None = None,
    ) -> Optional[Onboarding]:
        """Update user's onboarding status."""
        return self.calendar_repository.update_onboarding(user_id, calendar, completed)

    # New methods for original API structure
    def create_intervals_for_day(
        self,
        user_id: uuid.UUID,
        day_of_week: int,
        intervals: list[dict[str, str]],
    ) -> list[Calendar]:
        """Create multiple availability intervals for a day."""
        return self.calendar_repository.create_intervals_for_day(user_id, day_of_week, intervals)

    def get_grouped_availability(self, user_id: uuid.UUID) -> dict[int, list[dict[str, str]]]:
        """Get availability grouped by day of week."""
        return self.calendar_repository.get_grouped_availability(user_id)

    def generate_google_auth_url(self, client_id: str, redirect_uri: str) -> str:
        """Generate Google Calendar OAuth URL with custom client_id."""
        from urllib.parse import urlencode
        
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "https://www.googleapis.com/auth/calendar.readonly",
            "access_type": "offline",
            "prompt": "consent",
        }
        
        return f"{base_url}?{urlencode(params)}"

    def handle_google_oauth_callback(
        self,
        user_id: uuid.UUID,
        code: str,
        client_id: str,
        redirect_uri: str,
    ) -> GoogleCalendarAuth:
        """Handle Google OAuth callback and save tokens."""
        # In a real implementation, you would exchange the code for tokens
        # For now, we'll create a placeholder record
        return self.save_calendar_auth(user_id, "placeholder_access_token", "placeholder_refresh_token", 3600)

    def get_freebusy_data(
        self,
        user_id: uuid.UUID,
        start_datetime: str,
        end_datetime: str,
    ) -> dict[str, list[dict[str, str]]]:
        """Get freebusy data for a date range."""
        # In a real implementation, this would query Google Calendar API
        # For now, return placeholder data
        return {
            "busy_times": [],
            "free_times": [
                {"start_time": "09:00", "end_time": "17:00"}
            ]
        }