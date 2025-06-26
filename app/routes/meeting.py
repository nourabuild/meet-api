"""Meeting API routes with comprehensive meeting management."""

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.utils.delegate import CurrentUser, MeetingServiceDep
from app.utils.models import (
    MeetingCreate,
    MeetingPublic,
    MeetingsPublic,
    MeetingStatus,
    MeetingUpdate,
    Message,
    ParticipantBulkCreate,
    ParticipantCreate,
    ParticipantPublic,
    ParticipantStatus,
    ParticipantUpdate,
)

router = APIRouter()


# Meeting CRUD operations
@router.post("/", response_model=MeetingPublic)
def create_meeting(
    meeting_service: MeetingServiceDep,
    meeting_in: MeetingCreate,
    current_user: CurrentUser
) -> MeetingPublic:
    """Create a new meeting."""
    try:
        return meeting_service.create_meeting(meeting_in, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=MeetingsPublic)
def get_my_meetings(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    include_as_participant: bool = True
) -> MeetingsPublic:
    """Get all meetings for current user (owned or participating)."""
    return meeting_service.get_user_meetings(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_as_participant=include_as_participant
    )


@router.get("/search", response_model=MeetingsPublic)
def search_meetings(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = 0,
    limit: int = 20
) -> MeetingsPublic:
    """Search meetings by title or location."""
    try:
        return meeting_service.search_meetings(q, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
def get_meeting_stats(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> dict:
    """Get meeting statistics for current user."""
    return meeting_service.get_meeting_stats(current_user.id)


@router.get("/", response_model=MeetingsPublic)
def get_meetings(
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    owner_id: str | None = None,
    status: MeetingStatus | None = None
) -> MeetingsPublic:
    """Get meetings with optional filtering."""
    owner_uuid = None
    if owner_id:
        try:
            owner_uuid = uuid.UUID(owner_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid owner_id format")

    return meeting_service.get_meetings(
        skip=skip,
        limit=limit,
        owner_id=owner_uuid,
        status=status
    )


@router.get("/{meeting_id}", response_model=MeetingPublic)
def get_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> MeetingPublic:
    """Get meeting by ID."""
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.put("/{meeting_id}", response_model=MeetingPublic)
def update_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    meeting_in: MeetingUpdate,
    current_user: CurrentUser
) -> MeetingPublic:
    """Update meeting (owner only)."""
    try:
        return meeting_service.update_meeting(meeting_id, meeting_in, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> Message:
    """Delete meeting (owner only)."""
    try:
        success = meeting_service.delete_meeting(meeting_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return Message(message="Meeting deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Participant management
@router.get("/{meeting_id}/participants", response_model=list[ParticipantPublic])
def get_meeting_participants(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> list[ParticipantPublic]:
    """Get all participants for a meeting."""
    return meeting_service.get_meeting_participants(meeting_id)


@router.post("/{meeting_id}/participants", response_model=ParticipantPublic)
def add_participant(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    participant_in: ParticipantCreate,
    current_user: CurrentUser
) -> ParticipantPublic:
    """Add participant to meeting (owner/assigned user only)."""
    try:
        return meeting_service.add_participant(meeting_id, participant_in, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{meeting_id}/participants/bulk", response_model=list[ParticipantPublic])
def bulk_add_participants(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    participants_in: ParticipantBulkCreate,
    current_user: CurrentUser
) -> list[ParticipantPublic]:
    """Bulk add participants to meeting (owner/assigned user only)."""
    try:
        return meeting_service.bulk_add_participants(meeting_id, participants_in, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{meeting_id}/participants/{user_id}/status", response_model=ParticipantPublic)
def update_participant_status(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    status_update: ParticipantUpdate,
    current_user: CurrentUser
) -> ParticipantPublic:
    """Update participant status (self or owner)."""
    try:
        return meeting_service.update_participant_status(
            meeting_id, user_id, status_update.status, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{meeting_id}/participants/{user_id}")
def remove_participant(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> Message:
    """Remove participant from meeting (self or owner)."""
    try:
        success = meeting_service.remove_participant(meeting_id, user_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Participant not found")
        return Message(message="Participant removed successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Convenience endpoints for participant status updates
@router.post("/{meeting_id}/accept")
def accept_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> ParticipantPublic:
    """Accept meeting invitation."""
    try:
        return meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.ACCEPTED, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{meeting_id}/decline")
def decline_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> ParticipantPublic:
    """Decline meeting invitation."""
    try:
        return meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.DECLINED, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{meeting_id}/tentative")
def tentative_meeting(
    meeting_id: uuid.UUID,
    meeting_service: MeetingServiceDep,
    current_user: CurrentUser
) -> ParticipantPublic:
    """Mark meeting as tentative."""
    try:
        return meeting_service.update_participant_status(
            meeting_id, current_user.id, ParticipantStatus.TENTATIVE, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
