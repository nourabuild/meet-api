"""Meeting Routes
==============
Defines all endpoints related to meeting management, including:

Endpoints:
- POST /create: Create a new meeting with participants.
- GET /index: List meetings owned by or involving the current user.
- GET /requests: Retrieve meeting invitations awaiting response.
- GET /{meeting_id}: Fetch details of a specific meeting.
- POST /{meeting_id}/participants/add: Add participant to a meeting.
- POST /{meeting_id}/approve: Accept a meeting invitation.
- POST /{meeting_id}/decline: Decline a meeting invitation.
- POST /{meeting_id}/update: Update meeting details.
- POST /{meeting_id}/delete: Delete a meeting.
- POST /participants/{participant_id}/delete: Remove a participant from a meeting.
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.utils.delegate import (
    CurrentUser,
    MeetingServiceDep,
)
from app.utils.models import (
    MeetingCreate,
    MeetingObject,
    MeetingPublic,
    MeetingTypeBase,
    MeetingTypePublic,
    Message,
    ParticipantObject,
    ParticipantPublic,
    ParticipantStatus,
)

router = APIRouter()


@router.post("/create", response_model=MeetingPublic)
def create_meeting_with_participants(
    meeting_with_participants: MeetingCreate,
    current_user: CurrentUser,
    meeting_service: MeetingServiceDep,
    response: Response,
) -> MeetingPublic:
    """Create a new meeting with participants"""
    try:
        result = meeting_service.create_meeting_with_participants(
            meeting_with_participants, owner_id=current_user.id
        )
        response.status_code = status.HTTP_201_CREATED
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/index", response_model=list[MeetingPublic])
def get_my_meetings(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_as_participant: bool = Query(
        True, description="Include meetings where user is a participant"
    ),
    response: Response = None,
) -> list[MeetingPublic]:
    """Get all meetings"""
    try:
        meetings, _ = meeting_service.get_user_meetings(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            include_as_participant=include_as_participant,
        )
        response.status_code = status.HTTP_200_OK
        return meetings
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meetings",
        )


@router.get("/requests", response_model=list[MeetingPublic])
def get_my_meeting_requests(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    response: Response = None,
) -> list[MeetingPublic]:
    """Get pending meeting invitations"""
    response.status_code = status.HTTP_200_OK
    return meeting_service.get_user_meeting_requests(
        user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/{meeting_id}", response_model=MeetingPublic)
def get_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> MeetingPublic:
    """Show meeting details"""
    try:
        meeting = meeting_service.get_meeting(meeting_id, current_user.id)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found or access denied",
            )
        response.status_code = status.HTTP_200_OK
        return meeting
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/participants/add", response_model=ParticipantPublic)
def add_participant(
    meeting_id: uuid.UUID,
    participant_in: ParticipantObject,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> ParticipantPublic:
    """Add participant to meeting"""
    try:
        result = meeting_service.add_participant(
            meeting_id, participant_in, current_user.id
        )
        response.status_code = status.HTTP_200_OK
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/approve", response_model=Message)
def approve_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> Message:
    """Approve meeting invitation"""
    try:
        meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.ACCEPTED, current_user.id
        )
        response.status_code = status.HTTP_200_OK
        return Message(message="Meeting approved successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/decline", response_model=Message)
def decline_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> Message:
    """Decline meeting invitation"""
    try:
        meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.DECLINED, current_user.id
        )
        response.status_code = status.HTTP_200_OK
        return Message(message="Meeting declined successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/update", response_model=MeetingPublic)
def update_meeting(
    meeting_id: uuid.UUID,
    meeting_in: MeetingObject,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> MeetingPublic:
    """Update meeting"""
    try:
        updated = meeting_service.update_meeting(
            meeting_id, meeting_in, current_user.id
        )
        response.status_code = status.HTTP_200_OK
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/delete", response_model=Message)
def delete_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> Message:
    """Delete meeting"""
    try:
        success = meeting_service.delete_meeting(meeting_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found"
            )
        response.status_code = status.HTTP_200_OK
        return Message(message="Meeting deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/participants/{participant_id}/delete", response_model=Message)
def delete_participant_by_id(
    participant_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> Message:
    """Delete participant"""
    try:
        success = meeting_service.delete_participant_by_id(
            participant_id, current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
            )
        response.status_code = status.HTTP_200_OK
        return Message(message="Participant deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# MEETING TYPE ENDPOINTS
# ============================================================


@router.get("/types", response_model=list[MeetingTypePublic])
def list_meeting_types(
    meeting_service: MeetingServiceDep,
) -> list[MeetingTypePublic]:
    """List all available meeting types."""
    return meeting_service.list_meeting_types()


@router.get("/types/{type_id}", response_model=MeetingTypePublic)
def get_meeting_type(
    type_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
) -> MeetingTypePublic:
    """Get a specific meeting type by ID."""
    try:
        return meeting_service.get_meeting_type_by_id(type_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )


@router.post("/types", response_model=MeetingTypePublic)
def create_meeting_type(
    meeting_type_data: MeetingTypeBase,
    current_user: CurrentUser,
    meeting_service: MeetingServiceDep,
) -> MeetingTypePublic:
    """Create a new meeting type (admin only)."""
    # TODO: Add admin role check
    # if current_user.roles != UserRole.ADMIN:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only admins can create meeting types"
    #     )
    
    try:
        return meeting_service.create_meeting_type(meeting_type_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create meeting type: {str(e)}"
        )


@router.put("/types/{type_id}", response_model=MeetingTypePublic)
def update_meeting_type(
    type_id: uuid.UUID,
    meeting_type_data: MeetingTypeBase,
    current_user: CurrentUser,
    meeting_service: MeetingServiceDep,
) -> MeetingTypePublic:
    """Update a meeting type (admin only)."""
    # TODO: Add admin role check
    try:
        return meeting_service.update_meeting_type(type_id, meeting_type_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update meeting type: {str(e)}"
        )


@router.delete("/types/{type_id}", response_model=Message)
def delete_meeting_type(
    type_id: uuid.UUID,
    current_user: CurrentUser,
    meeting_service: MeetingServiceDep,
) -> Message:
    """Delete a meeting type (admin only)."""
    # TODO: Add admin role check
    try:
        success = meeting_service.delete_meeting_type(type_id)
        if success:
            return Message(message="Meeting type deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting type not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
