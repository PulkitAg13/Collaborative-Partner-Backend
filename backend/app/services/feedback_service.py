"""Feedback service — business logic for storing and processing feedback."""

from sqlalchemy.orm import Session

from app.agents.prompts import extract_preferences_from_feedback
from app.core.logging import get_logger
from app.db.models import Feedback, Message
from app.db.repositories.feedback import FeedbackRepository
from app.db.repositories.message import MessageRepository

logger = get_logger(__name__)


class FeedbackService:
    """Handles feedback ingestion and preference extraction."""

    def __init__(self, db: Session) -> None:
        self._fb_repo = FeedbackRepository(db)
        self._msg_repo = MessageRepository(db)

    def submit_feedback(
        self,
        conversation_id: str,
        message_id: str,
        rating: int,
        feedback_text: str | None,
    ) -> Feedback:
        """Validate, persist, and process feedback.

        After storing the raw feedback, extracts any user preferences from
        the feedback_text and upserts them into the UserPreference table
        so the agent can use them in subsequent messages.
        """
        # Validate message belongs to conversation
        msg: Message | None = self._msg_repo.get_by_id(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            raise ValueError("Message not found in this conversation.")

        fb = self._fb_repo.create_feedback(
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            feedback_text=feedback_text,
        )
        logger.info(
            "Feedback stored: id=%s conv=%s rating=%d", fb.id, conversation_id, rating
        )

        # Extract and persist preferences from feedback text
        if feedback_text:
            preferences = extract_preferences_from_feedback(feedback_text)
            for key, value in preferences.items():
                self._fb_repo.upsert_preference(
                    conversation_id=conversation_id,
                    key=key,
                    value=value,
                )
                logger.info(
                    "Preference upserted: conv=%s key=%s", conversation_id, key
                )

        return fb

    def get_preferences(self, conversation_id: str) -> dict[str, str]:
        """Return the current preferences for a conversation."""
        return self._fb_repo.get_preferences(conversation_id)
