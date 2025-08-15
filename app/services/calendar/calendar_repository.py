"""Calendar Repository
==================
Handles database operations for Google Calendar integration including
OAuth tokens, event synchronization, and calendar management.
"""

import uuid
from typing import Optional

from sqlmodel import Session, select

from app.utils.models import (
    GoogleCalendarAuth,
    CalendarEvent,
    Calendar,
    AvailabilityException,
    Onboarding,
)


class CalendarRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_calendar_auth(self, user_id: uuid.UUID) -> Optional[GoogleCalendarAuth]:
        """Get Google Calendar authentication for a user."""
        statement = select(GoogleCalendarAuth).where(GoogleCalendarAuth.user_id == user_id)
        return self.session.exec(statement).first()

    def create_calendar_auth(
        self,
        user_id: uuid.UUID,
        access_token: str,
        refresh_token: str,
        expires_at: int,
    ) -> GoogleCalendarAuth:
        """Create new calendar authentication record."""
        auth = GoogleCalendarAuth(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        self.session.add(auth)
        self.session.commit()
        self.session.refresh(auth)
        return auth

    def update_calendar_auth(
        self,
        auth: GoogleCalendarAuth,
        access_token: str,
        expires_at: int,
    ) -> GoogleCalendarAuth:
        """Update existing calendar authentication."""
        auth.access_token = access_token
        auth.expires_at = expires_at
        self.session.add(auth)
        self.session.commit()
        self.session.refresh(auth)
        return auth

    def delete_calendar_auth(self, user_id: uuid.UUID) -> bool:
        """Delete calendar authentication for a user."""
        statement = select(GoogleCalendarAuth).where(GoogleCalendarAuth.user_id == user_id)
        auth = self.session.exec(statement).first()
        if auth:
            self.session.delete(auth)
            self.session.commit()
            return True
        return False

    def get_calendar_events(self, user_id: uuid.UUID) -> list[CalendarEvent]:
        """Get all calendar events for a user."""
        statement = select(CalendarEvent).where(CalendarEvent.user_id == user_id)
        return list(self.session.exec(statement).all())

    def create_calendar_event(
        self,
        user_id: uuid.UUID,
        google_event_id: str,
        title: str,
        start_time: str,
        end_time: str,
        calendar_id: str,
    ) -> CalendarEvent:
        """Create a new calendar event record."""
        event = CalendarEvent(
            user_id=user_id,
            google_event_id=google_event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            calendar_id=calendar_id,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    # Calendar Availability Methods
    def get_user_availability(self, user_id: uuid.UUID) -> list[Calendar]:
        """Get all calendar availability for a user."""
        statement = select(Calendar).where(Calendar.user_id == user_id)
        return list(self.session.exec(statement).all())

    def create_availability(
        self,
        user_id: uuid.UUID,
        day_of_week: int,
        start_time: str,
        end_time: str,
    ) -> Calendar:
        """Create a new availability record."""
        availability = Calendar(
            user_id=user_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        self.session.add(availability)
        self.session.commit()
        self.session.refresh(availability)
        return availability

    def update_availability(
        self,
        availability_id: uuid.UUID,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> Optional[Calendar]:
        """Update an availability record."""
        statement = select(Calendar).where(Calendar.id == availability_id)
        availability = self.session.exec(statement).first()
        if availability:
            if start_time is not None:
                availability.start_time = start_time
            if end_time is not None:
                availability.end_time = end_time
            self.session.add(availability)
            self.session.commit()
            self.session.refresh(availability)
        return availability

    def delete_availability(self, availability_id: uuid.UUID) -> bool:
        """Delete an availability record."""
        statement = select(Calendar).where(Calendar.id == availability_id)
        availability = self.session.exec(statement).first()
        if availability:
            self.session.delete(availability)
            self.session.commit()
            return True
        return False

    # Availability Exception Methods
    def get_user_exceptions(self, user_id: uuid.UUID) -> list[AvailabilityException]:
        """Get all availability exceptions for a user."""
        statement = select(AvailabilityException).where(AvailabilityException.user_id == user_id)
        return list(self.session.exec(statement).all())

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
        """Create a new availability exception with recurrence support."""
        exception = AvailabilityException(
            user_id=user_id,
            exception_date=exception_date,
            recurrence_type=recurrence_type,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_available=is_available,
        )
        self.session.add(exception)
        self.session.commit()
        self.session.refresh(exception)
        return exception

    def delete_exception(self, exception_id: uuid.UUID) -> bool:
        """Delete an availability exception."""
        statement = select(AvailabilityException).where(AvailabilityException.id == exception_id)
        exception = self.session.exec(statement).first()
        if exception:
            self.session.delete(exception)
            self.session.commit()
            return True
        return False

    # Onboarding Methods
    def get_user_onboarding(self, user_id: uuid.UUID) -> Optional[Onboarding]:
        """Get user onboarding status."""
        statement = select(Onboarding).where(Onboarding.user_id == user_id)
        return self.session.exec(statement).first()

    def create_onboarding(self, user_id: uuid.UUID) -> Onboarding:
        """Create onboarding record for a user."""
        onboarding = Onboarding(user_id=user_id)
        self.session.add(onboarding)
        self.session.commit()
        self.session.refresh(onboarding)
        return onboarding

    def update_onboarding(
        self,
        user_id: uuid.UUID,
        calendar: bool | None = None,
        completed: bool | None = None,
    ) -> Optional[Onboarding]:
        """Update user onboarding status."""
        onboarding = self.get_user_onboarding(user_id)
        if not onboarding:
            onboarding = self.create_onboarding(user_id)
        
        if calendar is not None:
            onboarding.calendar = calendar
        if completed is not None:
            onboarding.completed = completed
            
        self.session.add(onboarding)
        self.session.commit()
        self.session.refresh(onboarding)
        return onboarding

    def create_intervals_for_day(
        self,
        user_id: uuid.UUID,
        day_of_week: int,
        intervals: list[dict[str, str]],
    ) -> list[Calendar]:
        """Create multiple availability intervals for a day."""
        # First, delete existing intervals for this day
        statement = select(Calendar).where(
            Calendar.user_id == user_id,
            Calendar.day_of_week == day_of_week
        )
        existing = list(self.session.exec(statement).all())
        for entry in existing:
            self.session.delete(entry)
        
        # Create new intervals
        created_intervals = []
        for interval in intervals:
            availability = Calendar(
                user_id=user_id,
                day_of_week=day_of_week,
                start_time=interval["start_time"],
                end_time=interval["end_time"],
            )
            self.session.add(availability)
            created_intervals.append(availability)
        
        self.session.commit()
        for interval in created_intervals:
            self.session.refresh(interval)
        
        return created_intervals

    def get_grouped_availability(self, user_id: uuid.UUID) -> dict[int, list[dict[str, str]]]:
        """Get availability grouped by day of week."""
        statement = select(Calendar).where(Calendar.user_id == user_id)
        availability = list(self.session.exec(statement).all())
        
        grouped = {}
        for avail in availability:
            if avail.day_of_week not in grouped:
                grouped[avail.day_of_week] = []
            grouped[avail.day_of_week].append({
                "start_time": avail.start_time,
                "end_time": avail.end_time,
            })
        
        return grouped