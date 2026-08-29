"""Pydantic schemas for the chat endpoint."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""

    conversation_id: str = Field(
        ...,
        description="UUID of an existing conversation",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The user's message to the agent",
        examples=["I want to plan my study schedule"],
    )


class ChatResponse(BaseModel):
    """Response from the agent after processing a user message."""

    conversation_id: str
    message_id: str
    response: str
    response_type: str = Field(
        description="One of: clarifying_question, guidance, plan, answer, acknowledgement",
        examples=["clarifying_question"],
    )
