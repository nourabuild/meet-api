"""Meeting API routes with comprehensive meeting management."""

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
    response: Response
) -> MeetingPublic:
    """Create a new meeting with participants"""
    try:
        result = meeting_service.create_meeting_with_participants(
            meeting_with_participants,
            owner_id=current_user.id
        )
        response.status_code = status.HTTP_201_CREATED
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/index", response_model=list[MeetingPublic])
def get_my_meetings(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_as_participant: bool = Query(True, description="Include meetings where user is a participant")
) -> list[MeetingPublic]:
    """Get all meetings"""
    try:
        meetings, _ = meeting_service.get_user_meetings(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            include_as_participant=include_as_participant
        )
        return meetings
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meetings"
        )


@router.get("/requests", response_model=list[ParticipantPublic])
def get_my_meeting_requests(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> list[ParticipantPublic]:
    """Get pending meeting invitations"""
    return meeting_service.get_user_meeting_requests(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get("/{meeting_id}", response_model=MeetingPublic)
def get_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> MeetingPublic:
    """Show meeting details"""
    try:
        meeting = meeting_service.get_meeting(meeting_id, current_user.id)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found or access denied"
            )
        return meeting
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{meeting_id}/participants/add", response_model=ParticipantPublic)
def add_participant(
    meeting_id: uuid.UUID,
    participant_in: ParticipantObject,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> ParticipantPublic:
    """Add participant to meeting"""
    try:
        return meeting_service.add_participant(meeting_id, participant_in, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{meeting_id}/approve", response_model=Message)
def approve_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> Message:
    """Approve meeting invitation"""
    try:
        meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.ACCEPTED, current_user.id
        )
        return Message(message="Meeting approved successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{meeting_id}/decline", response_model=Message)
def decline_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> Message:
    """Decline meeting invitation"""
    try:
        meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.DECLINED, current_user.id
        )
        return Message(message="Meeting declined successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{meeting_id}/update", response_model=MeetingPublic)
def update_meeting(
    meeting_id: uuid.UUID,
    meeting_in: MeetingObject,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> MeetingPublic:
    """Update meeting"""
    try:
        return meeting_service.update_meeting(meeting_id, meeting_in, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{meeting_id}/delete", response_model=Message)
def delete_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> Message:
    """Delete meeting"""
    try:
        success = meeting_service.delete_meeting(meeting_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        return Message(message="Meeting deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/participants/{participant_id}/delete", response_model=Message)
def delete_participant_by_id(
    participant_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> Message:
    """Delete participant"""
    try:
        success = meeting_service.delete_participant_by_id(participant_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found"
            )
        return Message(message="Participant deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
