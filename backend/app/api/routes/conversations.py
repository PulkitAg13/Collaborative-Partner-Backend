"""Conversation management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationCreateResponse,
    ConversationHistoryResponse,
    DeleteResponse,
    MessageOut,
)
from app.services.conversation_service import ConversationService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Conversations"])


@router.post(
    "/conversations",
    response_model=ConversationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Starts a new conversation session for a user.",
)
async def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
) -> ConversationCreateResponse:
    """Create a conversation and return its ID."""
    logger.info("Request: create conversation user=%s", payload.user_id)
    svc = ConversationService(db)
    conv = svc.create_conversation(user_id=payload.user_id)
    return ConversationCreateResponse(
        conversation_id=conv.id,
        user_id=conv.user_id,
        created_at=conv.created_at,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history",
    description="Returns the full message history for a conversation.",
    responses={404: {"description": "Conversation not found"}},
)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationHistoryResponse:
    """Retrieve conversation metadata and all messages."""
    svc = ConversationService(db)
    conv = svc.get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    messages = svc.get_messages(conversation_id)
    return ConversationHistoryResponse(
        conversation_id=conv.id,
        user_id=conv.user_id,
        created_at=conv.created_at,
        messages=[
            MessageOut(
                message_id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=DeleteResponse,
    summary="Delete a conversation",
    description="Permanently deletes a conversation and all its messages, feedback, and preferences.",
    responses={404: {"description": "Conversation not found"}},
)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> DeleteResponse:
    """Delete a conversation by ID."""
    logger.info("Request: delete conversation id=%s", conversation_id)
    svc = ConversationService(db)
    deleted = svc.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return DeleteResponse(success=True)
