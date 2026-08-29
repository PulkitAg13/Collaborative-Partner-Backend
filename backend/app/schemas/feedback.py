"""Pydantic schemas for the feedback endpoint."""

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """Request body for submitting feedback on an assistant message."""

    conversation_id: str = Field(
        ...,
        description="UUID of the conversation this feedback belongs to",
    )
    message_id: str = Field(
        ...,
        description="UUID of the assistant message being rated",
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 (poor) to 5 (excellent)",
        examples=[4],
    )
    feedback_text: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional free-text comment from the user",
        examples=["This was useful. Give me more practical examples next time."],
    )


class FeedbackResponse(BaseModel):
    """Response after feedback is recorded."""

    success: bool
    feedback_id: str
