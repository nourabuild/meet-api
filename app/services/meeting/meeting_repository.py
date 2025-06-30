"""Meeting repository for database operations with optimized joins."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Session, and_, desc, func, or_, select

from app.utils.models import (
    Meeting,
    MeetingObject,
    Participant,
    ParticipantObject,
    ParticipantStatus,
    User,
)


class MeetingRepository:

    def __init__(self, session: Session):
        self.session = session

    def create_meeting_with_participants(
        self,
        meeting_dict: dict,
        participants: list[ParticipantObject]
    ) -> Meeting:
        try:
            meeting = Meeting(**meeting_dict)
            self.session.add(meeting)
            self.session.flush()  

            for participant_data in participants:
                user = self.session.get(User, participant_data.user_id)
                if not user:
                    raise ValueError("User does not exist")

                participant = Participant(
                    meeting_id=meeting.id,
                    user_id=participant_data.user_id,
                    status=participant_data.status
                )
                self.session.add(participant)

            self.session.commit()
            self.session.refresh(meeting)
            return meeting

        except Exception:
            self.session.rollback()
            raise

    def get_user_meetings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_as_participant: bool = True
    ) -> tuple[list[Meeting], int]:
        filters = [Meeting.owner_id == user_id]

        if include_as_participant:
            participant_meeting_ids = (
                select(Participant.meeting_id)
                .where(
                    and_(
                        Participant.user_id == user_id,
                        Participant.status != ParticipantStatus.NEW
                    )
                )
            )
            filters.append(Meeting.id.in_(participant_meeting_ids))

        count_query = select(func.count(Meeting.id.distinct())).where(or_(*filters))
        total_count = self.session.exec(count_query).one()

        query = (
            select(Meeting)
            .where(or_(*filters))
            .order_by(Meeting.start_time.desc())
            .offset(skip)
            .limit(limit)
        )

        meetings = self.session.exec(query).all()
        return meetings, total_count

    def get_user_meeting_requests(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Participant], int]:
        count_query = (
            select(func.count(Participant.id))
            .where(
                and_(
                    Participant.user_id == user_id,
                    Participant.status == ParticipantStatus.NEW
                )
            )
        )
        total_count = self.session.exec(count_query).one()

        query = (
            select(Participant, User)
            .join(User, Participant.user_id == User.id)
            .where(
                and_(
                    Participant.user_id == user_id,
                    Participant.status == ParticipantStatus.NEW
                )
            )
            .order_by(desc(Participant.created_at))
            .offset(skip)
            .limit(limit)
        )

        results = self.session.exec(query).all()
        participants = [result[0] for result in results]
        return participants, total_count


    def update_participant_status(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        status: ParticipantStatus
    ) -> Participant | None:
        participant = self.session.exec(
            select(Participant).where(
                and_(
                    Participant.meeting_id == meeting_id,
                    Participant.user_id == user_id
                )
            )
        ).first()

        if not participant:
            return None

        participant.status = status
        participant.updated_at = datetime.now(UTC)

        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)
        return participant

    def get_meeting_by_id(self, meeting_id: uuid.UUID) -> Meeting | None:
        return self.session.get(Meeting, meeting_id)

    def add_participant(self, meeting_id: uuid.UUID, participant_data: ParticipantObject) -> Participant | None:
        meeting = self.session.get(Meeting, meeting_id)
        if not meeting:
            return None

        user = self.session.get(User, participant_data.user_id)
        if not user:
            return None

        existing = self.session.exec(
            select(Participant).where(
                and_(
                    Participant.meeting_id == meeting_id,
                    Participant.user_id == participant_data.user_id
                )
            )
        ).first()

        if existing:
            raise ValueError("User is already a participant in this meeting")

        db_participant = Participant(
            meeting_id=meeting_id,
            user_id=participant_data.user_id,
            status=participant_data.status,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        self.session.add(db_participant)
        self.session.commit()
        self.session.refresh(db_participant)
        return db_participant

    def update_meeting(self, meeting_id: uuid.UUID, meeting_data: MeetingObject) -> Meeting | None:
        db_meeting = self.session.get(Meeting, meeting_id)
        if not db_meeting:
            return None

        update_data = meeting_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(UTC)

        for field, value in update_data.items():
            setattr(db_meeting, field, value)

        self.session.add(db_meeting)
        self.session.commit()
        self.session.refresh(db_meeting)
        return db_meeting

    def delete_meeting(self, meeting_id: uuid.UUID) -> bool:
        db_meeting = self.session.get(Meeting, meeting_id)
        if not db_meeting:
            return False

        participants = self.session.exec(
            select(Participant).where(Participant.meeting_id == meeting_id)
        ).all()

        for participant in participants:
            self.session.delete(participant)

        self.session.delete(db_meeting)
        self.session.commit()
        return True

    def get_participant_by_id(self, participant_id: uuid.UUID) -> Participant | None:
        return self.session.get(Participant, participant_id)

    def delete_participant_by_id(self, participant_id: uuid.UUID) -> bool:
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return False

        self.session.delete(participant)
        self.session.commit()
        return True
