"""Chat route — the core agent interaction endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.collaborative_agent import AgentService, create_agent_service
from app.core.logging import get_logger
from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import ChatService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])


def get_agent_service() -> AgentService:
    """FastAPI dependency — returns the configured AgentService singleton."""
    return create_agent_service()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the Collaborative Partner",
    description=(
        "Sends a user message to the agent. "
        "The agent uses the full conversation history and any stored user "
        "preferences to generate a contextually aware, adaptive response."
    ),
    responses={
        404: {"description": "Conversation not found"},
        422: {"description": "Validation error"},
        500: {"description": "Agent error"},
    },
)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    agent: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    """Handle a chat turn: validate → history → agent → store → respond."""
    logger.info(
        "Request: chat conv=%s preview='%.60s'",
        payload.conversation_id,
        payload.message,
    )

    svc = ChatService(db=db, agent=agent)

    try:
        assistant_msg, response_type = await svc.chat(
            conversation_id=payload.conversation_id,
            user_message=payload.message,
        )
    except ValueError as exc:
        error_str = str(exc)
        if "not found" in error_str.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except RuntimeError:
        # Agent errors are already logged in ChatService
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The agent encountered an error. Please try again.",
        )

    return ChatResponse(
        conversation_id=payload.conversation_id,
        message_id=assistant_msg.id,
        response=assistant_msg.content,
        response_type=response_type,
    )
