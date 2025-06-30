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

        meeting_data = meeting.model_dump()
        meeting_data["owner_id"] = owner_id

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

    def get_user_meeting_requests(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[ParticipantPublic]:
        participants, _ = self.repository.get_user_meeting_requests(
            user_id=user_id, skip=skip, limit=limit
        )

        return [
            ParticipantPublic.model_validate(participant)
            for participant in participants
        ]

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

        return ParticipantPublic.model_validate(updated_participant)

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

        updated_meeting = self.repository.update_meeting(meeting_id, meeting_data)
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

        return self.repository.delete_participant_by_id(participant_id)
