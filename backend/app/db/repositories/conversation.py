"""Conversation repository — data-access layer for Conversation records."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Conversation


class ConversationRepository:
    """Encapsulates all database operations for Conversation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: str) -> Conversation:
        """Create and persist a new conversation."""
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Return a conversation by its ID, or None if not found."""
        return self.db.get(Conversation, conversation_id)

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation by ID. Returns True if it existed."""
        conv = self.get_by_id(conversation_id)
        if conv is None:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    def touch(self, conversation_id: str) -> None:
        """Update the updated_at timestamp (called after each chat message)."""
        conv = self.get_by_id(conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            self.db.commit()
