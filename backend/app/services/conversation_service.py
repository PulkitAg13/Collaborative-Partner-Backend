"""Conversation service — business logic for conversation management."""

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import Conversation, Message
from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.message import MessageRepository

logger = get_logger(__name__)


class ConversationService:
    """Handles conversation lifecycle operations."""

    def __init__(self, db: Session) -> None:
        self._conv_repo = ConversationRepository(db)
        self._msg_repo = MessageRepository(db)

    def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation for the given user."""
        conv = self._conv_repo.create(user_id=user_id)
        logger.info("Conversation created: id=%s user=%s", conv.id, user_id)
        return conv

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Return a conversation or None if it does not exist."""
        return self._conv_repo.get_by_id(conversation_id)

    def get_messages(self, conversation_id: str) -> list[Message]:
        """Return all messages for a conversation in chronological order."""
        return self._msg_repo.list_by_conversation(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all related data. Returns True if found."""
        deleted = self._conv_repo.delete(conversation_id)
        if deleted:
            logger.info("Conversation deleted: id=%s", conversation_id)
        return deleted
