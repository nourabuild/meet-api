"""Meeting service for business logic and validation."""

import uuid
from datetime import datetime, UTC

from app.services.meeting.meeting_repository import MeetingRepository
from app.utils.models import (
    Meeting,
    MeetingCreate,
    MeetingPublic,
    MeetingPublic,
    MeetingStatus,
    MeetingUpdate,
    MeetingWithParticipantsCreate,
    MeetingRequestsPublic,
    MeetingRequestPublic,
    Participant,
    ParticipantBulkCreate,
    ParticipantCreate,
    ParticipantPublic,
    ParticipantStatus,
    UserPublic,
    MeetingsPublic,
)


class MeetingService:
    """Service layer for meeting operations with business logic."""

    def __init__(self, repository: MeetingRepository):
        self.repository = repository

    def create_meeting(self, meeting_data: MeetingCreate, owner_id: uuid.UUID) -> MeetingPublic:
        """Create a new meeting with validation."""
        # Validate start time is in the future
        if meeting_data.start_time <= datetime.now(UTC):
            raise ValueError("Meeting start time must be in the future")

        # Create meeting data with owner_id
        meeting_dict = meeting_data.model_dump()
        meeting_dict["owner_id"] = owner_id

        # Create meeting
        db_meeting = self.repository.create_meeting(Meeting(**meeting_dict))

        # Get meeting with relationships for response
        meeting_with_relationships = self.repository.get_meeting_by_id(db_meeting.id)
        return self._convert_to_public(meeting_with_relationships)

    def create_meeting_with_participants(
        self, 
        meeting_with_participants: MeetingWithParticipantsCreate, 
        owner_id: uuid.UUID
    ) -> MeetingPublic:
        """Create a new meeting with participants in a single transaction."""
        # Validate start time is in the future
        if meeting_with_participants.meeting.start_time <= datetime.now(UTC):
            raise ValueError("Meeting start time must be in the future")

        # Check if owner is included in the participants list
        if any(p.user_id == owner_id for p in meeting_with_participants.participants):
            raise ValueError("You cannot add yourself as a participant")

        # Filter out any participants that are the owner
        non_owner_participants = [p for p in meeting_with_participants.participants if p.user_id != owner_id]
        if not non_owner_participants:
            raise ValueError("You must add at least one participant other than yourself.")

        # Create meeting data with owner_id
        meeting_dict = meeting_with_participants.meeting.model_dump()
        meeting_dict["owner_id"] = owner_id

        # Always add the owner as ACCEPTED, and only non-owner participants from the request
        participants = list(non_owner_participants)
        participants.append(ParticipantCreate(user_id=owner_id, status=ParticipantStatus.ACCEPTED))

        db_meeting = self.repository.create_meeting_with_participants(
            meeting_dict,  # Pass as dict
            participants
        )

        # Get meeting with relationships for response
        meeting_with_relationships = self.repository.get_meeting_by_id(db_meeting.id)
        return self._convert_to_public(meeting_with_relationships)

    def get_meeting(self, meeting_id: uuid.UUID) -> MeetingPublic | None:
        """Get meeting by ID."""
        db_meeting = self.repository.get_meeting_by_id(meeting_id)
        if not db_meeting:
            return None
        return self._convert_to_public(db_meeting)

    def get_meetings(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: uuid.UUID | None = None,
        status: MeetingStatus | None = None
    ) -> MeetingsPublic:
        """Get meetings with pagination and filtering."""
        meetings, total_count = self.repository.get_meetings(
            skip=skip,
            limit=limit,
            owner_id=owner_id,
            status=status
        )

        return MeetingsPublic(
            data=[self._convert_to_public(meeting) for meeting in meetings],
            count=total_count
        )

    def get_user_meetings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_as_participant: bool = True
    ) -> MeetingsPublic:
        """Get all meetings for a user (owned or participating)."""
        meetings, total_count = self.repository.get_user_meetings(
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_as_participant=include_as_participant
        )

        return MeetingsPublic(
            data=[self._convert_to_public(meeting) for meeting in meetings],
            count=total_count
        )

    def update_meeting(
        self,
        meeting_id: uuid.UUID,
        meeting_data: MeetingUpdate,
        user_id: uuid.UUID
    ) -> MeetingPublic:
        """Update meeting with ownership validation."""
        # Get current meeting
        current_meeting = self.repository.get_meeting_by_id(meeting_id, include_relationships=False)
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

        # Get updated meeting with relationships
        meeting_with_relationships = self.repository.get_meeting_by_id(meeting_id)
        return self._convert_to_public(meeting_with_relationships)

    def delete_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete meeting with ownership validation."""
        # Get current meeting
        current_meeting = self.repository.get_meeting_by_id(meeting_id, include_relationships=False)
        if not current_meeting:
            raise ValueError("Meeting not found")

        # Check if user is owner
        if current_meeting.owner_id != user_id:
            raise ValueError("Only meeting owner can delete meeting")

        return self.repository.delete_meeting(meeting_id)

    def add_participant(
        self,
        meeting_id: uuid.UUID,
        participant_data: ParticipantCreate,
        requester_id: uuid.UUID
    ) -> ParticipantPublic:
        """Add participant to meeting with permission validation."""
        # Get meeting
        meeting = self.repository.get_meeting_by_id(meeting_id, include_relationships=False)
        if not meeting:
            raise ValueError("Meeting not found")

        # Check if requester is owner or assigned user
        if meeting.owner_id != requester_id and meeting.assigned_to != requester_id:
            raise ValueError("Only meeting owner or assigned user can add participants")

        # Add participant
        try:
            db_participant = self.repository.add_participant(meeting_id, participant_data)
            if not db_participant:
                raise ValueError("Failed to add participant")

            # Get participant with user data
            participants = self.repository.get_meeting_participants(meeting_id)
            for p in participants:
                if p.id == db_participant.id:
                    return self._convert_participant_to_public(p)

            raise ValueError("Participant added but not found in response")

        except ValueError as e:
            raise e

    def bulk_add_participants(
        self,
        meeting_id: uuid.UUID,
        participants_data: ParticipantBulkCreate,
        requester_id: uuid.UUID
    ) -> list[ParticipantPublic]:
        """Bulk add participants to meeting."""
        # Get meeting
        meeting = self.repository.get_meeting_by_id(meeting_id, include_relationships=False)
        if not meeting:
            raise ValueError("Meeting not found")

        # Check permissions
        if meeting.owner_id != requester_id and meeting.assigned_to != requester_id:
            raise ValueError("Only meeting owner or assigned user can add participants")

        # Extract user IDs
        user_ids = [p.user_id for p in participants_data.participants]

        # Bulk add
        new_participants = self.repository.bulk_add_participants(meeting_id, user_ids)

        return [self._convert_participant_to_public(p) for p in new_participants]

    def update_participant_status(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        status: ParticipantStatus,
        requester_id: uuid.UUID
    ) -> ParticipantPublic:
        """Update participant status."""
        # Users can update their own status, or meeting owner can update any status
        meeting = self.repository.get_meeting_by_id(meeting_id, include_relationships=False)
        if not meeting:
            raise ValueError("Meeting not found")

        if requester_id != user_id and meeting.owner_id != requester_id:
            raise ValueError("You can only update your own participation status")

        updated_participant = self.repository.update_participant_status(meeting_id, user_id, status)
        if not updated_participant:
            raise ValueError("Participant not found")

        # Get participant with user data
        participants = self.repository.get_meeting_participants(meeting_id)
        for p in participants:
            if p.user_id == user_id:
                return self._convert_participant_to_public(p)

        raise ValueError("Participant updated but not found in response")

    def remove_participant(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        requester_id: uuid.UUID
    ) -> bool:
        """Remove participant from meeting."""
        # Get meeting
        meeting = self.repository.get_meeting_by_id(meeting_id, include_relationships=False)
        if not meeting:
            raise ValueError("Meeting not found")

        # Check permissions (owner can remove anyone, users can remove themselves)
        if meeting.owner_id != requester_id and requester_id != user_id:
            raise ValueError("You can only remove yourself or be removed by meeting owner")

        # Cannot remove the meeting owner
        if user_id == meeting.owner_id:
            raise ValueError("Cannot remove meeting owner from participants")

        return self.repository.remove_participant(meeting_id, user_id)

    def remove_participant_by_id(
        self,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID
    ) -> bool:
        """Remove participant by participant ID."""
        # Get the participant to check permissions
        target_participant = self.repository.get_participant_by_id(participant_id)
        if not target_participant:
            raise ValueError("Participant not found")
        
        # Get meeting to check permissions
        meeting = self.repository.get_meeting_by_id(target_participant.meeting_id, include_relationships=False)
        if not meeting:
            raise ValueError("Meeting not found")

        # Check permissions (owner can remove anyone, users can remove themselves)
        if meeting.owner_id != requester_id and requester_id != target_participant.user_id:
            raise ValueError("You can only remove yourself or be removed by meeting owner")

        # Cannot remove the meeting owner
        if target_participant.user_id == meeting.owner_id:
            raise ValueError("Cannot remove meeting owner from participants")

        return self.repository.remove_participant_by_id(participant_id)

    def get_meeting_participants(self, meeting_id: uuid.UUID) -> list[ParticipantPublic]:
        """Get all participants for a meeting."""
        participants = self.repository.get_meeting_participants(meeting_id)
        return [self._convert_participant_to_public(p) for p in participants]

    def search_meetings(
        self,
        query: str,
        user_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> MeetingsPublic:
        """Search meetings by title or location."""
        if len(query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")

        meetings, total_count = self.repository.search_meetings(query, user_id, skip, limit)

        return MeetingsPublic(
            data=[self._convert_to_public(meeting) for meeting in meetings],
            count=total_count
        )

    def get_meeting_stats(self, user_id: uuid.UUID) -> dict:
        """Get meeting statistics for a user."""
        return self.repository.get_meeting_stats(user_id)

    def get_user_meeting_requests(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> MeetingRequestsPublic:
        """Get meeting requests (pending invitations) for a user."""
        participants, total_count = self.repository.get_user_meeting_requests(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

        meeting_requests = []
        for participant in participants:
            meeting_requests.append(self._convert_participant_to_request_public(participant))

        return MeetingRequestsPublic(
            data=meeting_requests,
            count=total_count
        )

    def _convert_to_public(self, meeting: Meeting) -> MeetingPublic:
        """Convert database meeting to public meeting with relationships."""
        # Convert participants
        participants = []
        for participant in meeting.participants:
            participants.append(self._convert_participant_to_public(participant))

        return MeetingPublic(
            id=meeting.id,
            title=meeting.title,
            appointed_by=meeting.appointed_by,
            assigned_to=meeting.assigned_to,
            owner_id=meeting.owner_id,
            type=meeting.type,
            status=meeting.status,
            start_time=meeting.start_time,
            location=meeting.location,
            location_url=meeting.location_url,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
            participants=participants
        )

    def _convert_participant_to_public(self, participant: Participant) -> ParticipantPublic:
        """Convert database participant to public participant with user."""
        user = UserPublic.model_validate(participant.user)

        return ParticipantPublic(
            id=participant.id,
            meeting_id=participant.meeting_id,
            user_id=participant.user_id,
            status=participant.status,
            created_at=participant.created_at,
            updated_at=participant.updated_at,
            user=user
        )

    def _convert_participant_to_request_public(self, participant: Participant) -> MeetingRequestPublic:
        """Convert database participant to meeting request public with meeting and user data."""
        # Convert the meeting to public format
        meeting_public = self._convert_to_public(participant.meeting)
        
        # Convert the user to public format
        user_public = UserPublic.model_validate(participant.user)

        return MeetingRequestPublic(
            id=participant.id,
            meeting_id=participant.meeting_id,
            user_id=participant.user_id,
            status=participant.status,
            created_at=participant.created_at,
            updated_at=participant.updated_at,
            meeting=meeting_public,
            user=user_public
        )
