"""Meeting service for business logic and validation."""

from typing import List, Tuple
import uuid
from datetime import UTC, datetime

from app.services.meeting.meeting_repository import MeetingRepository
from app.utils.models import (
    MeetingObject,
    MeetingPublic,
    MeetingCreate,
    ParticipantObject,
    ParticipantPublic,
    ParticipantStatus,
)


class MeetingService:
    """Service layer for meeting operations with business logic."""

    def __init__(self, repository: MeetingRepository):
        self.repository = repository

    def create_meeting_with_participants(
        self,
        meeting_with_participants: MeetingCreate,
        owner_id: uuid.UUID
    ) -> MeetingPublic:
        """Create a new meeting with participants in a single transaction."""

        meeting = meeting_with_participants.meeting
        now = datetime.now(UTC)

        # Validate start time
        if meeting.start_time <= now:
            raise ValueError("Meeting start time must be in the future")

        # Validate participants: owner must not be in participants and at least one other participant required
        participant_user_ids = {p.user_id for p in meeting_with_participants.participants}
        if owner_id in participant_user_ids:
            raise ValueError("You cannot add yourself as a participant")

        if not participant_user_ids:
            raise ValueError("You must add at least one participant.")

        # Compose meeting dict with owner
        meeting_data = meeting.model_dump()
        meeting_data["owner_id"] = owner_id

        # Add owner as ACCEPTED participant
        participants = List(meeting_with_participants.participants) + [
            ParticipantObject(user_id=owner_id, status=ParticipantStatus.ACCEPTED)
        ]

        # Create meeting and participants in DB
        db_meeting = self.repository.create_meeting_with_participants(
            meeting_data,
            participants
        )

        return MeetingPublic.model_validate(db_meeting)


    def get_user_meetings(
            self,
            user_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100,
            include_as_participant: bool = True
        ) -> Tuple[List[MeetingPublic], int]:
            """Get all meetings for a user (owned or participating) with total count."""
            meetings, total_count = self.repository.get_user_meetings(
                user_id=user_id,
                skip=skip,
                limit=limit,
                include_as_participant=include_as_participant
            )
            
            meeting_publics = [MeetingPublic.model_validate(meeting) for meeting in meetings]
            return meeting_publics, total_count
        

    def get_user_meeting_requests(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ParticipantPublic]:
        """Get meeting requests (pending invitations) for a user."""
        participants, _ = self.repository.get_user_meeting_requests(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

        return [ParticipantPublic.model_validate(participant) for participant in participants]


    def get_meeting(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> MeetingPublic | None:
        """Get meeting by ID."""
        meeting = self.repository.get_meeting_by_id(meeting_id)
        if not meeting:
            return None
        
        return MeetingPublic.model_validate(meeting)

   

    def add_participant(
        self,
        meeting_id: uuid.UUID,
        participant_data: ParticipantObject,
        requester_id: uuid.UUID
    ) -> ParticipantPublic:
        """Add participant to meeting with permission validation."""
        # Get meeting
        meeting = self.repository.get_meeting_by_id(meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        # Check if requester is owner
        if meeting.owner_id != requester_id:
            raise ValueError("Only meeting owner can add participants")

        # Add participant
        db_participant = self.repository.add_participant(meeting_id, participant_data)
        if not db_participant:
            raise ValueError("Failed to add participant")

        return ParticipantPublic.model_validate(db_participant)

   

    def update_participant_status(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        status: ParticipantStatus,
        requester_id: uuid.UUID
    ) -> ParticipantPublic:
        """Update participant status."""
        # Users can update their own status, or meeting owner can update any status
        meeting = self.repository.get_meeting_by_id(meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        if requester_id != user_id and meeting.owner_id != requester_id:
            raise ValueError("You can only update your own participation status")

        updated_participant = self.repository.update_participant_status(meeting_id, user_id, status)
        if not updated_participant:
            raise ValueError("Participant not found")

        return ParticipantPublic.model_validate(updated_participant)

   

    def update_meeting(
        self,
        meeting_id: uuid.UUID,
        meeting_data: MeetingObject,
        user_id: uuid.UUID
    ) -> MeetingPublic:
        """Update meeting with ownership validation."""
        # Get current meeting
        current_meeting = self.repository.get_meeting_by_id(meeting_id)
        if not current_meeting:
            raise ValueError("Meeting not found")

        # Check if user is owner
        if current_meeting.owner_id != user_id:
            raise ValueError("Only meeting owner can update meeting")

        # Validate start time if being updated
        if meeting_data.start_time and meeting_data.start_time <= datetime.now(UTC):
            raise ValueError("Meeting start time must be in the future")

        # Update meeting
        updated_meeting = self.repository.update_meeting(meeting_id, meeting_data)
        if not updated_meeting:
            raise ValueError("Failed to update meeting")

        return MeetingPublic.model_validate(updated_meeting)

   

    def delete_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete meeting with ownership validation."""
        # Get current meeting
        current_meeting = self.repository.get_meeting_by_id(meeting_id)
        if not current_meeting:
            raise ValueError("Meeting not found")

        # Check if user is owner
        if current_meeting.owner_id != user_id:
            raise ValueError("Only meeting owner can delete meeting")

        return self.repository.delete_meeting(meeting_id)