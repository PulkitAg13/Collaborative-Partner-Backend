"""Feedback repository — data-access layer for Feedback and UserPreference records."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Feedback, UserPreference


class FeedbackRepository:
    """Encapsulates all database operations for Feedback and UserPreference."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Feedback ──────────────────────────────────────────────────────────────

    def create_feedback(
        self,
        conversation_id: str,
        message_id: str,
        rating: int,
        feedback_text: str | None,
    ) -> Feedback:
        """Persist a feedback record and return it."""
        fb = Feedback(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            feedback_text=feedback_text,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def list_by_conversation(self, conversation_id: str) -> list[Feedback]:
        """Return all feedback for a conversation."""
        return (
            self.db.query(Feedback)
            .filter(Feedback.conversation_id == conversation_id)
            .order_by(Feedback.created_at)
            .all()
        )

    # ── UserPreference ────────────────────────────────────────────────────────

    def upsert_preference(
        self,
        conversation_id: str,
        key: str,
        value: str,
    ) -> UserPreference:
        """Create or update a preference key for a conversation."""
        pref = (
            self.db.query(UserPreference)
            .filter(
                UserPreference.conversation_id == conversation_id,
                UserPreference.key == key,
            )
            .first()
        )
        now = datetime.now(timezone.utc)
        if pref is None:
            pref = UserPreference(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                key=key,
                value=value,
                created_at=now,
                updated_at=now,
            )
            self.db.add(pref)
        else:
            pref.value = value
            pref.updated_at = now
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def get_preferences(self, conversation_id: str) -> dict[str, str]:
        """Return all preferences for a conversation as a plain dict."""
        prefs = (
            self.db.query(UserPreference)
            .filter(UserPreference.conversation_id == conversation_id)
            .all()
        )
        return {p.key: p.value for p in prefs}
