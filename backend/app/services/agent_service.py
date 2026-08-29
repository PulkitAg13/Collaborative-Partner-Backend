"""Agent service orchestrator — coordinates agent calls with conversation state."""

from sqlalchemy.orm import Session

from app.agents.collaborative_agent import AgentService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import Message
from app.db.repositories.conversation import ConversationRepository
from app.db.repositories.feedback import FeedbackRepository
from app.db.repositories.message import MessageRepository

logger = get_logger(__name__)
settings = get_settings()


class ChatService:
    """Orchestrates a single chat turn:

    1. Validate conversation exists.
    2. Load conversation history.
    3. Load active preferences.
    4. Store user message.
    5. Call agent.
    6. Store assistant message.
    7. Return assistant message.
    """

    def __init__(self, db: Session, agent: AgentService) -> None:
        self._conv_repo = ConversationRepository(db)
        self._msg_repo = MessageRepository(db)
        self._fb_repo = FeedbackRepository(db)
        self._agent = agent

    async def chat(
        self,
        conversation_id: str,
        user_message: str,
    ) -> Message:
        """Process a user message and return the assistant's reply Message."""
        # 1. Validate conversation
        conv = self._conv_repo.get_by_id(conversation_id)
        if conv is None:
            raise ValueError("Conversation not found.")

        # Enforce message length limit
        max_len = settings.max_message_length
        if len(user_message) > max_len:
            raise ValueError(
                f"Message exceeds maximum length of {max_len} characters."
            )

        logger.info("Chat turn: conv=%s message_preview='%.60s'", conversation_id, user_message)

        # 2. Load history (before storing current message)
        history_msgs = self._msg_repo.list_by_conversation(conversation_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_msgs
        ]

        # 3. Load active preferences
        preferences = self._fb_repo.get_preferences(conversation_id)
        if preferences:
            logger.info("Active preferences for conv=%s: %s", conversation_id, list(preferences.keys()))

        # 4. Store user message
        self._msg_repo.create(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )

        # 5. Call agent
        logger.info("Sending request to agent: conv=%s", conversation_id)
        try:
            response_text, response_type = await self._agent.generate_response(
                conversation_history=conversation_history,
                user_message=user_message,
                preferences=preferences,
            )
        except RuntimeError as exc:
            logger.error("Agent error for conv=%s: %s", conversation_id, exc)
            raise

        logger.info(
            "Agent response: conv=%s type=%s preview='%.60s'",
            conversation_id,
            response_type,
            response_text,
        )

        # 6. Store assistant message
        assistant_msg = self._msg_repo.create(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
        )

        # 7. Touch conversation timestamp
        self._conv_repo.touch(conversation_id)

        return assistant_msg, response_type
