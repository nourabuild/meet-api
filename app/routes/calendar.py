"""Calendar Routes
===============
Provides endpoints for Google Calendar integration including OAuth flow,
authentication status, event synchronization, availability management,
exceptions, and onboarding tracking.

Endpoints:
- GET /auth: Get calendar authentication status and OAuth URL
- POST /auth: Save calendar authentication after OAuth callback
- DELETE /auth: Remove calendar authentication
- GET /events: Get synchronized calendar events
- GET /availability: Get user's calendar availability
- POST /availability: Create new availability
- PUT /availability/{id}: Update availability
- DELETE /availability/{id}: Delete availability
- GET /exceptions: Get availability exceptions
- POST /exceptions: Create availability exception
- DELETE /exceptions/{id}: Delete availability exception
- GET /onboarding: Get onboarding status
- PUT /onboarding: Update onboarding status
"""

import uuid
from fastapi import APIRouter, Response, status
from app.utils.delegate import CurrentUser, CalendarServiceDep
from app.utils.models import (
    CalendarAuthResponse,
    CalendarEventsResponse,
    CalendarAvailabilityResponse,
    CalendarAvailabilityCreate,
    CalendarAvailabilityUpdate,
    AvailabilityExceptionsResponse,
    AvailabilityExceptionCreate,
    OnboardingPublic,
    OnboardingUpdate,
)

router = APIRouter()


@router.get("/auth", response_model=CalendarAuthResponse)
def get_calendar_auth_status(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> CalendarAuthResponse:
    """Get calendar authentication status and OAuth URL if not connected."""
    response.status_code = status.HTTP_200_OK
    
    is_connected = calendar_service.is_calendar_connected(current_user.id)
    oauth_url = None if is_connected else calendar_service.get_oauth_url()
    
    return CalendarAuthResponse(
        is_connected=is_connected,
        oauth_url=oauth_url,
    )


@router.post("/auth")
def save_calendar_auth(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    access_token: str,
    refresh_token: str,
    expires_at: int,
    response: Response,
) -> dict[str, str]:
    """Save calendar authentication after OAuth callback."""
    calendar_service.save_calendar_auth(
        current_user.id, access_token, refresh_token, expires_at
    )
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Calendar authentication saved successfully"}


@router.delete("/auth")
def remove_calendar_auth(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> dict[str, str]:
    """Remove calendar authentication for the current user."""
    success = calendar_service.remove_calendar_auth(current_user.id)
    
    if success:
        response.status_code = status.HTTP_200_OK
        return {"message": "Calendar authentication removed successfully"}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "No calendar authentication found"}


@router.get("/events", response_model=CalendarEventsResponse)
def get_calendar_events(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> CalendarEventsResponse:
    """Get all synchronized calendar events for the current user."""
    events = calendar_service.get_calendar_events(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    return CalendarEventsResponse(
        events=[
            {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "calendar_id": event.calendar_id,
            }
            for event in events
        ],
        count=len(events),
    )


# Availability Management Endpoints
@router.get("/availability", response_model=CalendarAvailabilityResponse)
def get_calendar_availability(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> CalendarAvailabilityResponse:
    """Get user's calendar availability."""
    availability = calendar_service.get_user_availability(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    return CalendarAvailabilityResponse(
        availability=[
            {
                "id": avail.id,
                "weekday": avail.weekday,
                "start_time": avail.start_time,
                "end_time": avail.end_time,
            }
            for avail in availability
        ],
        count=len(availability),
    )


@router.post("/availability")
def create_calendar_availability(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    availability_data: CalendarAvailabilityCreate,
    response: Response,
) -> dict[str, str]:
    """Create new calendar availability."""
    calendar_service.create_availability(
        current_user.id,
        availability_data.weekday,
        availability_data.start_time,
        availability_data.end_time,
    )
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Availability created successfully"}


@router.put("/availability/{availability_id}")
def update_calendar_availability(
    availability_id: uuid.UUID,
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    availability_data: CalendarAvailabilityUpdate,
    response: Response,
) -> dict[str, str]:
    """Update calendar availability."""
    updated = calendar_service.update_availability(
        availability_id,
        availability_data.start_time,
        availability_data.end_time,
    )
    
    if updated:
        response.status_code = status.HTTP_200_OK
        return {"message": "Availability updated successfully"}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Availability not found"}


@router.delete("/availability/{availability_id}")
def delete_calendar_availability(
    availability_id: uuid.UUID,
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> dict[str, str]:
    """Delete calendar availability."""
    success = calendar_service.delete_availability(availability_id)
    
    if success:
        response.status_code = status.HTTP_200_OK
        return {"message": "Availability deleted successfully"}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Availability not found"}


# Availability Exception Endpoints
@router.get("/exceptions", response_model=AvailabilityExceptionsResponse)
def get_availability_exceptions(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> AvailabilityExceptionsResponse:
    """Get user's availability exceptions."""
    exceptions = calendar_service.get_user_exceptions(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    return AvailabilityExceptionsResponse(
        exceptions=[
            {
                "id": exc.id,
                "date": exc.date,
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
    """Create availability exception."""
    calendar_service.create_exception(
        current_user.id,
        str(exception_data.date),
        exception_data.start_time,
        exception_data.end_time,
        exception_data.is_available,
    )
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Availability exception created successfully"}


@router.delete("/exceptions/{exception_id}")
def delete_availability_exception(
    exception_id: uuid.UUID,
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> dict[str, str]:
    """Delete availability exception."""
    success = calendar_service.delete_exception(exception_id)
    
    if success:
        response.status_code = status.HTTP_200_OK
        return {"message": "Availability exception deleted successfully"}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Availability exception not found"}


# Onboarding Endpoints
@router.get("/onboarding", response_model=OnboardingPublic)
def get_onboarding_status(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    response: Response,
) -> OnboardingPublic:
    """Get user's onboarding status."""
    onboarding = calendar_service.get_user_onboarding(current_user.id)
    response.status_code = status.HTTP_200_OK
    
    if onboarding:
        return OnboardingPublic(
            id=onboarding.id,
            calendar=onboarding.calendar,
            completed=onboarding.completed,
        )
    else:
        # Create default onboarding if none exists
        new_onboarding = calendar_service.update_onboarding(current_user.id)
        return OnboardingPublic(
            id=new_onboarding.id,
            calendar=new_onboarding.calendar,
            completed=new_onboarding.completed,
        )


@router.put("/onboarding")
def update_onboarding_status(
    current_user: CurrentUser,
    calendar_service: CalendarServiceDep,
    onboarding_data: OnboardingUpdate,
    response: Response,
) -> dict[str, str]:
    """Update user's onboarding status."""
    calendar_service.update_onboarding(
        current_user.id,
        onboarding_data.calendar,
        onboarding_data.completed,
    )
    response.status_code = status.HTTP_200_OK
    return {"message": "Onboarding status updated successfully"}