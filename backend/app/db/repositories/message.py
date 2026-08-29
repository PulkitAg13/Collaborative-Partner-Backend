"""Message repository — data-access layer for Message records."""

import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from app.db.models import Message


class MessageRepository:
    """Encapsulates all database operations for Message."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        conversation_id: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> Message:
        """Persist a new message and return it."""
        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_by_id(self, message_id: str) -> Message | None:
        """Return a message by its ID, or None."""
        return self.db.get(Message, message_id)

    def list_by_conversation(self, conversation_id: str) -> list[Message]:
        """Return all messages for a conversation, ordered by creation time."""
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )
