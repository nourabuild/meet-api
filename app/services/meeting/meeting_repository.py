"""Meeting repository for database operations with optimized joins."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, and_, or_, select

from app.utils.models import (
    Meeting,
    MeetingCreate,
    MeetingStatus,
    MeetingUpdate,
    Participant,
    ParticipantCreate,
    ParticipantStatus,
    User,
)


class MeetingRepository:
    """Repository for meeting-related database operations with optimized joins."""

    def __init__(self, session: Session):
        self.session = session

    # Meeting CRUD operations
    def create_meeting(self, meeting_data: MeetingCreate) -> Meeting:
        """Create a new meeting."""
        db_meeting = Meeting.model_validate(meeting_data, update={
            "created_at": datetime.now(datetime.now(timezone.utc)),
            "updated_at": datetime.now(datetime.now(timezone.utc))
        })
        self.session.add(db_meeting)
        self.session.commit()
        self.session.refresh(db_meeting)
        return db_meeting

    def get_meeting_by_id(self, meeting_id: uuid.UUID, include_relationships: bool = True) -> Meeting | None:
        """Get meeting by ID with optimized loading of relationships."""
        if include_relationships:
            # Optimized query with eager loading
            statement = (
                select(Meeting)
                .where(Meeting.id == meeting_id)
                .options(
                    selectinload(Meeting.participants).selectinload(Participant.user),
                    joinedload(Meeting.owner),
                    joinedload(Meeting.appointed_by_user),
                    joinedload(Meeting.assigned_to_user)
                )
            )
            return self.session.exec(statement).first()
        else:
            return self.session.get(Meeting, meeting_id)

    def get_meetings(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: uuid.UUID | None = None,
        status: MeetingStatus | None = None,
        include_relationships: bool = True
    ) -> tuple[list[Meeting], int]:
        """Get meetings with optional filtering and optimized joins."""
        # Build base query
        query = select(Meeting)
        count_query = select(Meeting.id)

        # Apply filters
        filters = []
        if owner_id:
            filters.append(Meeting.owner_id == owner_id)
        if status:
            filters.append(Meeting.status == status)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Add optimized loading for relationships
        if include_relationships:
            query = query.options(
                selectinload(Meeting.participants).selectinload(Participant.user),
                joinedload(Meeting.owner),
                joinedload(Meeting.appointed_by_user),
                joinedload(Meeting.assigned_to_user)
            )

        # Execute queries
        query = query.order_by(Meeting.start_time.desc()).offset(skip).limit(limit)
        meetings = self.session.exec(query).all()
        total_count = len(self.session.exec(count_query).all())

        return meetings, total_count

    def get_user_meetings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_as_participant: bool = True
    ) -> tuple[list[Meeting], int]:
        """Get meetings where user is owner, assigned to, or participant."""
        # Build complex query for user meetings
        filters = [Meeting.owner_id == user_id]

        if include_as_participant:
            # Add subquery for participant meetings
            participant_meeting_ids = (
                select(Participant.meeting_id)
                .where(Participant.user_id == user_id)
            )
            filters.append(Meeting.id.in_(participant_meeting_ids))

        query = (
            select(Meeting)
            .where(or_(*filters))
            .options(
                selectinload(Meeting.participants).selectinload(Participant.user),
                joinedload(Meeting.owner),
                joinedload(Meeting.appointed_by_user),
                joinedload(Meeting.assigned_to_user)
            )
            .order_by(Meeting.start_time.desc())
            .offset(skip)
            .limit(limit)
        )

        count_query = (
            select(Meeting.id)
            .where(or_(*filters))
        )

        meetings = self.session.exec(query).all()
        total_count = len(self.session.exec(count_query).all())

        return meetings, total_count

    def update_meeting(self, meeting_id: uuid.UUID, meeting_data: MeetingUpdate) -> Meeting | None:
        """Update meeting data."""
        db_meeting = self.session.get(Meeting, meeting_id)
        if not db_meeting:
            return None

        update_data = meeting_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(datetime.now(timezone.utc))

        for field, value in update_data.items():
            setattr(db_meeting, field, value)

        self.session.add(db_meeting)
        self.session.commit()
        self.session.refresh(db_meeting)
        return db_meeting

    def delete_meeting(self, meeting_id: uuid.UUID) -> bool:
        """Delete meeting and all participants."""
        db_meeting = self.session.get(Meeting, meeting_id)
        if not db_meeting:
            return False

        # Delete participants first (due to foreign key constraints)
        self.session.exec(
            select(Participant).where(Participant.meeting_id == meeting_id)
        )
        for participant in self.session.exec(
            select(Participant).where(Participant.meeting_id == meeting_id)
        ).all():
            self.session.delete(participant)

        # Delete meeting
        self.session.delete(db_meeting)
        self.session.commit()
        return True

    # Participant operations
    def add_participant(self, meeting_id: uuid.UUID, participant_data: ParticipantCreate) -> Participant | None:
        """Add participant to meeting."""
        # Check if meeting exists
        meeting = self.session.get(Meeting, meeting_id)
        if not meeting:
            return None

        # Check if user exists
        user = self.session.get(User, participant_data.user_id)
        if not user:
            return None

        # Check if participant already exists
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

        # Create participant
        db_participant = Participant(
            meeting_id=meeting_id,
            user_id=participant_data.user_id,
            status=participant_data.status,
            created_at=datetime.now(datetime.now(timezone.utc)),
            updated_at=datetime.now(datetime.now(timezone.utc))
        )

        self.session.add(db_participant)
        self.session.commit()
        self.session.refresh(db_participant)
        return db_participant

    def update_participant_status(
        self,
        meeting_id: uuid.UUID,
        user_id: uuid.UUID,
        status: ParticipantStatus
    ) -> Participant | None:
        """Update participant status."""
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
        participant.updated_at = datetime.now(datetime.now(timezone.utc))

        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)
        return participant

    def remove_participant(self, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Remove participant from meeting."""
        participant = self.session.exec(
            select(Participant).where(
                and_(
                    Participant.meeting_id == meeting_id,
                    Participant.user_id == user_id
                )
            )
        ).first()

        if not participant:
            return False

        self.session.delete(participant)
        self.session.commit()
        return True

    def get_meeting_participants(self, meeting_id: uuid.UUID) -> list[Participant]:
        """Get all participants for a meeting with user data."""
        return self.session.exec(
            select(Participant)
            .where(Participant.meeting_id == meeting_id)
            .options(selectinload(Participant.user))
        ).all()

    def bulk_add_participants(self, meeting_id: uuid.UUID, user_ids: list[uuid.UUID]) -> list[Participant]:
        """Bulk add participants to meeting."""
        # Check if meeting exists
        meeting = self.session.get(Meeting, meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        # Get existing participants to avoid duplicates
        existing_participants = self.session.exec(
            select(Participant.user_id).where(Participant.meeting_id == meeting_id)
        ).all()
        existing_user_ids = set(existing_participants)

        # Create new participants
        new_participants = []
        for user_id in user_ids:
            if user_id not in existing_user_ids:
                # Verify user exists
                user = self.session.get(User, user_id)
                if user:
                    participant = Participant(
                        meeting_id=meeting_id,
                        user_id=user_id,
                        status=ParticipantStatus.NEW,
                        created_at=datetime.now(datetime.now(timezone.utc)),
                        updated_at=datetime.now(datetime.now(timezone.utc))
                    )
                    new_participants.append(participant)

        if new_participants:
            self.session.add_all(new_participants)
            self.session.commit()
            for participant in new_participants:
                self.session.refresh(participant)

        return new_participants

    # Analytics and statistics
    def get_meeting_stats(self, user_id: uuid.UUID) -> dict:
        """Get meeting statistics for a user."""
        # Count meetings as owner
        owned_meetings = self.session.exec(
            select(Meeting.id).where(Meeting.owner_id == user_id)
        ).all()

        # Count meetings as participant
        participant_meetings = self.session.exec(
            select(Participant.meeting_id).where(Participant.user_id == user_id)
        ).all()

        # Count by status
        pending_meetings = self.session.exec(
            select(Meeting.id).where(
                and_(
                    Meeting.owner_id == user_id,
                    Meeting.status == MeetingStatus.PENDING
                )
            )
        ).all()

        return {
            "owned_meetings_count": len(owned_meetings),
            "participating_meetings_count": len(participant_meetings),
            "pending_meetings_count": len(pending_meetings),
            "total_meetings_count": len(set(owned_meetings + participant_meetings))
        }

    def search_meetings(
        self,
        query: str,
        user_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Meeting], int]:
        """Search meetings by title or location."""
        search_filter = or_(
            Meeting.title.ilike(f"%{query}%"),
            Meeting.location.ilike(f"%{query}%")
        )

        base_query = select(Meeting).where(search_filter)
        count_query = select(Meeting.id).where(search_filter)

        # Add user filter if provided
        if user_id:
            user_filter = or_(
                Meeting.owner_id == user_id,
                Meeting.id.in_(
                    select(Participant.meeting_id).where(Participant.user_id == user_id)
                )
            )
            base_query = base_query.where(user_filter)
            count_query = count_query.where(user_filter)

        # Add relationships and pagination
        query_with_relationships = (
            base_query
            .options(
                selectinload(Meeting.participants).selectinload(Participant.user),
                joinedload(Meeting.owner),
                joinedload(Meeting.appointed_by_user),
                joinedload(Meeting.assigned_to_user)
            )
            .order_by(Meeting.start_time.desc())
            .offset(skip)
            .limit(limit)
        )

        meetings = self.session.exec(query_with_relationships).all()
        total_count = len(self.session.exec(count_query).all())

        return meetings, total_count
