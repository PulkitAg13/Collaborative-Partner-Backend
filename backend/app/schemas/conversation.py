"""Pydantic schemas for conversation endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Request body for creating a new conversation."""

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Identifier for the user starting this conversation",
        examples=["demo-user"],
    )


class ConversationCreateResponse(BaseModel):
    """Response after a conversation is created."""

    conversation_id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    """A single message within a conversation."""

    message_id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationHistoryResponse(BaseModel):
    """Full conversation history including all messages."""

    conversation_id: str
    user_id: str
    created_at: datetime
    messages: list[MessageOut]


class DeleteResponse(BaseModel):
    """Response for delete/reset operations."""

    success: bool
