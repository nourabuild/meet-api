"""Meeting Service
===============
Implements business logic and validation for meetings and participants,
including creation, updates, deletions, and access control.
"""

import uuid
from datetime import UTC, datetime

from app.services.meeting.meeting_repository import MeetingRepository
from app.utils.models import (
    MeetingCreate,
    MeetingObject,
    MeetingPublic,
    MeetingStatus,
    MeetingType,
    MeetingTypeBase,
    MeetingTypePublic,
    ParticipantObject,
    ParticipantPublic,
    ParticipantStatus,
)


class MeetingService:
    def __init__(self, repository: MeetingRepository):
        self.repository = repository

    def create_meeting_with_participants(
        self, meeting_with_participants: MeetingCreate, owner_id: uuid.UUID
    ) -> MeetingPublic:
        meeting = meeting_with_participants.meeting
        now = datetime.now(UTC)

        if meeting.start_time <= now:
            raise ValueError("Meeting start time must be in the future")

        participant_user_ids = {
            p.user_id for p in meeting_with_participants.participants
        }
        if owner_id in participant_user_ids:
            raise ValueError("You cannot add yourself as a participant")

        if not participant_user_ids:
            raise ValueError("You must add at least one participant.")

        # Get or create meeting type
        meeting_type = self.repository.get_meeting_type_by_title(meeting.type)
        if not meeting_type:
            meeting_type_data = MeetingTypeBase(title=meeting.type)
            meeting_type = self.repository.create_meeting_type(meeting_type_data)

        meeting_data = meeting.model_dump()
        meeting_data["owner_id"] = owner_id
        # Replace 'type' with 'type_id'
        meeting_data.pop("type", None)  # Remove the type string
        meeting_data["type_id"] = meeting_type.id  # Add the type_id UUID

        participants = list(meeting_with_participants.participants) + [
            ParticipantObject(user_id=owner_id, status=ParticipantStatus.ACCEPTED)
        ]

        db_meeting = self.repository.create_meeting_with_participants(
            meeting_data, participants
        )

        return MeetingPublic.model_validate(db_meeting)

    def get_user_meetings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_as_participant: bool = True,
    ) -> tuple[list[MeetingPublic], int]:
        meetings, total_count = self.repository.get_user_meetings(
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_as_participant=include_as_participant,
        )

        meeting_publics = [
            MeetingPublic.model_validate(meeting) for meeting in meetings
        ]
        return meeting_publics, total_count

    def get_past_meetings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_as_participant: bool = True,
    ) -> tuple[list[MeetingPublic], int]:
        meetings, total_count = self.repository.get_past_meetings(
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_as_participant=include_as_participant,
        )

        meeting_publics = [
            MeetingPublic.model_validate(meeting) for meeting in meetings
        ]
        return meeting_publics, total_count

    def get_user_meeting_requests(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[MeetingPublic]:
        meetings, _ = self.repository.get_user_meeting_requests(
            user_id=user_id, skip=skip, limit=limit
        )

        return [MeetingPublic.model_validate(meeting) for meeting in meetings]

    def get_meeting(
        self, meeting_id: uuid.UUID, user_id: uuid.UUID
    ) -> MeetingPublic | None:
        meeting = self.repository.get_meeting_by_id(meeting_id)
        if not meeting:
            return None

        return MeetingPublic.model_validate(meeting)

    def add_participant(
        self,
        meeting_id: uuid.UUID,
        participant_data: ParticipantObject,
        requester_id: uuid.UUID,
    ) -> ParticipantPublic:
        meeting = self.repository.get_meeting_by_id(meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        if meeting.owner_id != requester_id:
            raise ValueError("Only meeting owner can add participants")

        db_participant = self.repository.add_participant(meeting_id, participant_data)
        if not db_participant:
            raise ValueError("Failed to add participant")

        # Check if meeting status should be updated based on participant responses
        self._update_meeting_status_based_on_participants(meeting_id)

        return ParticipantPublic.model_validate(db_participant)

    def update_participant_status(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        status: ParticipantStatus,
        requester_id: uuid.UUID,
    ) -> ParticipantPublic:
        meeting = self.repository.get_meeting_by_id(meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        if requester_id != user_id and meeting.owner_id != requester_id:
            raise ValueError("You can only update your own participation status")

        updated_participant = self.repository.update_participant_status(
            meeting_id, user_id, status
        )
        if not updated_participant:
            raise ValueError("Participant not found")

        # Check if meeting status should be updated based on participant responses
        self._update_meeting_status_based_on_participants(meeting_id)

        return ParticipantPublic.model_validate(updated_participant)

    def _update_meeting_status_based_on_participants(
        self, meeting_id: uuid.UUID
    ) -> None:
        """Update meeting status based on all participants' responses."""
        participants = self.repository.get_meeting_participants(meeting_id)

        if not participants:
            return

        # Count participant statuses
        declined_count = sum(
            1 for p in participants if p.status == ParticipantStatus.DECLINED
        )
        accepted_count = sum(
            1 for p in participants if p.status == ParticipantStatus.ACCEPTED
        )
        total_participants = len(participants)

        new_status = None

        # If any participant declined, cancel the meeting
        if declined_count > 0:
            new_status = MeetingStatus.CANCELED
        # If all participants accepted, approve the meeting
        elif accepted_count == total_participants:
            new_status = MeetingStatus.APPROVED
        # Otherwise, keep it as NEW (some participants haven't responded yet)

        # Update meeting status if it needs to change
        if new_status:
            current_meeting = self.repository.get_meeting_by_id(meeting_id)
            if current_meeting and current_meeting.status != new_status:
                self.repository.update_meeting(meeting_id, {"status": new_status})

    def update_meeting(
        self, meeting_id: uuid.UUID, meeting_data: MeetingObject, user_id: uuid.UUID
    ) -> MeetingPublic:
        current_meeting = self.repository.get_meeting_by_id(meeting_id)
        if not current_meeting:
            raise ValueError("Meeting not found")

        if current_meeting.owner_id != user_id:
            raise ValueError("Only meeting owner can update meeting")

        if meeting_data.start_time and meeting_data.start_time <= datetime.now(UTC):
            raise ValueError("Meeting start time must be in the future")

        # Resolve meeting type string to type_id if type is provided
        if hasattr(meeting_data, "type") and meeting_data.type:
            meeting_type = self.repository.get_meeting_type_by_title(meeting_data.type)
            if not meeting_type:
                meeting_type_data = MeetingTypeBase(title=meeting_data.type)
                meeting_type = self.repository.create_meeting_type(meeting_type_data)

            # Convert to dict, remove type, add type_id
            update_data = meeting_data.model_dump()
            update_data.pop("type", None)
            update_data["type_id"] = meeting_type.id

            # Create a new MeetingObject-like dict for the repository
            meeting_data_dict = update_data
        else:
            meeting_data_dict = meeting_data.model_dump()

        updated_meeting = self.repository.update_meeting(meeting_id, meeting_data_dict)
        if not updated_meeting:
            raise ValueError("Failed to update meeting")

        return MeetingPublic.model_validate(updated_meeting)

    def delete_meeting(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        current_meeting = self.repository.get_meeting_by_id(meeting_id)
        if not current_meeting:
            raise ValueError("Meeting not found")

        if current_meeting.owner_id != user_id:
            raise ValueError("Only meeting owner can delete meeting")

        return self.repository.delete_meeting(meeting_id)

    def delete_participant_by_id(
        self, participant_id: uuid.UUID, requester_id: uuid.UUID
    ) -> bool:
        target_participant = self.repository.get_participant_by_id(participant_id)
        if not target_participant:
            raise ValueError("Participant not found")

        meeting = self.repository.get_meeting_by_id(target_participant.meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        if (
            meeting.owner_id != requester_id
            and requester_id != target_participant.user_id
        ):
            raise ValueError(
                "You can only remove yourself or be removed by meeting owner"
            )

        if target_participant.user_id == meeting.owner_id:
            raise ValueError("Cannot remove meeting owner from participants")

        result = self.repository.delete_participant_by_id(participant_id)

        if result:
            # Check if meeting status should be updated after participant removal
            self._update_meeting_status_based_on_participants(
                target_participant.meeting_id
            )

        return result

    # ============================================================
    # MEETING TYPE METHODS
    # ============================================================

    def create_meeting_type(
        self, meeting_type_data: MeetingTypeBase
    ) -> MeetingTypePublic:
        """Create a new meeting type."""
        meeting_type = self.repository.create_meeting_type(meeting_type_data)
        return MeetingTypePublic.model_validate(meeting_type)

    def get_meeting_type_by_id(self, meeting_type_id: uuid.UUID) -> MeetingTypePublic:
        """Get a meeting type by ID."""
        meeting_type = self.repository.get_meeting_type_by_id(meeting_type_id)
        if not meeting_type:
            raise ValueError("Meeting type not found")
        return MeetingTypePublic.model_validate(meeting_type)

    def get_meeting_type_by_title(self, title: str) -> MeetingTypePublic | None:
        """Get a meeting type by title."""
        meeting_type = self.repository.get_meeting_type_by_title(title)
        if meeting_type:
            return MeetingTypePublic.model_validate(meeting_type)
        return None

    def list_meeting_types(self) -> list[MeetingTypePublic]:
        """List all meeting types."""
        meeting_types = self.repository.list_meeting_types()
        return [MeetingTypePublic.model_validate(mt) for mt in meeting_types]

    def update_meeting_type(
        self, meeting_type_id: uuid.UUID, meeting_type_data: MeetingTypeBase
    ) -> MeetingTypePublic:
        """Update a meeting type."""
        existing_type = self.repository.get_meeting_type_by_id(meeting_type_id)
        if not existing_type:
            raise ValueError("Meeting type not found")

        meeting_type = self.repository.update_meeting_type(
            meeting_type_id, meeting_type_data
        )
        return MeetingTypePublic.model_validate(meeting_type)

    def delete_meeting_type(self, meeting_type_id: uuid.UUID) -> bool:
        """Delete a meeting type."""
        existing_type = self.repository.get_meeting_type_by_id(meeting_type_id)
        if not existing_type:
            raise ValueError("Meeting type not found")

        # Check if the meeting type is in use
        if self.repository.is_meeting_type_in_use(meeting_type_id):
            raise ValueError("Cannot delete meeting type that is in use")

        return self.repository.delete_meeting_type(meeting_type_id)
