"""Calendar Routes
===============
Provides endpoints for calendar management matching the original API structure.

Endpoints:
- GET /entries: Get all calendar entries
- GET /grouped: Get calendar entries grouped by day of week
- POST /intervals: Create availability intervals for a specific day
- GET /exceptions: Get availability exceptions
- POST /exceptions: Create availability exception with recurrence support
- GET /google/auth-url: Get Google Calendar OAuth URL
- POST /google/connect: Handle OAuth callback and connect Google Calendar
- GET /google/freebusy: Get Google Calendar freebusy data
"""

import uuid
from typing import Annotated
from fastapi import APIRouter, Response, status, Query
from app.utils.delegate import CurrentUser, CalendarServiceDep
from app.utils.models import (
    CalendarEntriesResponse,
    CalendarGroupedResponse,
    CalendarIntervalCreate,
    AvailabilityExceptionsResponse,
    AvailabilityExceptionCreate,
    GoogleCalendarAuthUrl,
    GoogleCalendarConnect,
    FreeBusyResponse,
    TimeInterval,
    OnboardingPublic,
)

router = APIRouter()


@router.get("/entries/list", response_model=CalendarEntriesResponse)
def get_calendar_entries(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> CalendarEntriesResponse:
    """Get all calendar entries for the current user."""
    availability = calendar_service.get_user_availability(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    return CalendarEntriesResponse(
        entries=[
            {
                "id": avail.id,
                "day_of_week": avail.day_of_week,
                "start_time": avail.start_time,
                "end_time": avail.end_time,
            }
            for avail in availability
        ],
        count=len(availability),
    )


@router.get("/grouped", response_model=CalendarGroupedResponse)
def get_calendar_grouped(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> CalendarGroupedResponse:
    """Get calendar entries grouped by day of week."""
    grouped_data = calendar_service.get_grouped_availability(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    # Convert to TimeInterval objects
    grouped_intervals = {}
    for day, intervals in grouped_data.items():
        grouped_intervals[day] = [
            TimeInterval(start_time=interval["start_time"], end_time=interval["end_time"])
            for interval in intervals
        ]
    
    return CalendarGroupedResponse(grouped_by_day=grouped_intervals)


@router.post("/intervals")
def create_calendar_intervals(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    interval_data: CalendarIntervalCreate,
    response: Response,
) -> dict[str, str]:
    """Create availability intervals for a specific day."""
    # Convert TimeInterval objects to dicts
    intervals_dict = [
        {"start_time": interval.start_time, "end_time": interval.end_time}
        for interval in interval_data.intervals
    ]
    
    calendar_service.create_intervals_for_day(
        current_user.id,
        interval_data.day_of_week,
        intervals_dict,
    )
    
    # Update onboarding status to mark calendar as completed
    calendar_service.update_onboarding(current_user.id, calendar=True)
    
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Calendar intervals created successfully"}


@router.get("/exceptions", response_model=AvailabilityExceptionsResponse)
def get_availability_exceptions(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> AvailabilityExceptionsResponse:
    """Get availability exceptions for the current user."""
    exceptions = calendar_service.get_user_exceptions(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    return AvailabilityExceptionsResponse(
        exceptions=[
            {
                "id": exc.id,
                "date": exc.exception_date,
                "start_time": exc.start_time,
                "end_time": exc.end_time,
                "is_available": exc.is_available,
            }
            for exc in exceptions
        ],
        count=len(exceptions),
    )


@router.post("/exceptions")
def create_availability_exception(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    exception_data: AvailabilityExceptionCreate,
    response: Response,
) -> dict[str, str]:
    """Create availability exception with recurrence support."""
    calendar_service.create_exception(
        current_user.id,
        str(exception_data.exception_date),
        exception_data.recurrence_type,
        exception_data.day_of_week,
        exception_data.start_time,
        exception_data.end_time,
        exception_data.is_available,
    )
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Availability exception created successfully"}


# Google Calendar Integration Endpoints
@router.get("/google/auth-url", response_model=GoogleCalendarAuthUrl)
def get_google_calendar_auth_url(
    client_id: Annotated[str, Query()],
    redirect_uri: Annotated[str, Query()],
    calendar_service: CalendarServiceDep,
    response: Response,
) -> GoogleCalendarAuthUrl:
    """Get Google Calendar OAuth authorization URL."""
    auth_url = calendar_service.generate_google_auth_url(client_id, redirect_uri)
    response.status_code = status.HTTP_200_OK
    
    return GoogleCalendarAuthUrl(auth_url=auth_url)


@router.post("/google/connect")
def connect_google_calendar(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    client_id: Annotated[str, Query()],
    redirect_uri: Annotated[str, Query()],
    response: Response,
) -> dict[str, str]:
    """Handle Google Calendar OAuth callback and connect account."""
    calendar_service.handle_google_oauth_callback(
        current_user.id, code, client_id, redirect_uri
    )
    response.status_code = status.HTTP_200_OK
    return {"message": "Google Calendar connected successfully"}


@router.get("/google/freebusy", response_model=FreeBusyResponse)
def get_google_calendar_freebusy(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    start_datetime: Annotated[str, Query()],
    end_datetime: Annotated[str, Query()],
    response: Response,
) -> FreeBusyResponse:
    """Get Google Calendar freebusy data for a date range."""
    freebusy_data = calendar_service.get_freebusy_data(
        current_user.id, start_datetime, end_datetime
    )
    response.status_code = status.HTTP_200_OK
    
    return FreeBusyResponse(
        busy_times=[
            TimeInterval(start_time=time["start_time"], end_time=time["end_time"])
            for time in freebusy_data["busy_times"]
        ],
        free_times=[
            TimeInterval(start_time=time["start_time"], end_time=time["end_time"])
            for time in freebusy_data["free_times"]
        ],
    )


# Onboarding Endpoint
@router.get("/onboarding/check", response_model=OnboardingPublic)
def get_onboarding_status(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> OnboardingPublic:
    """Get user's calendar onboarding status."""
    onboarding = calendar_service.get_user_onboarding(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    if onboarding:
        # Check if user has completed calendar setup by having availability entries
        availability = calendar_service.get_user_availability(current_user.id)
        has_calendar_entries = len(availability) > 0
        
        # Update onboarding status and completion based on calendar entries
        if has_calendar_entries and not onboarding.calendar:
            onboarding = calendar_service.update_onboarding(current_user.id, calendar=True, completed=True)
        elif has_calendar_entries and onboarding.calendar and not onboarding.completed:
            onboarding = calendar_service.update_onboarding(current_user.id, completed=True)
        
        return OnboardingPublic(
            id=onboarding.id,
            calendar=onboarding.calendar,
            completed=onboarding.completed,
        )
    else:
        # Create new onboarding record
        new_onboarding = calendar_service.update_onboarding(current_user.id)
        return OnboardingPublic(
            id=new_onboarding.id,
            calendar=new_onboarding.calendar,
            completed=new_onboarding.completed,
        )