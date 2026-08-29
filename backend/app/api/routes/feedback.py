"""Feedback route — collect and process user feedback on agent responses."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import get_db
from app.db.repositories.conversation import ConversationRepository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Feedback"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on an agent response",
    description=(
        "Records user feedback (rating + optional text) for a specific agent message. "
        "The backend automatically extracts preferences from the feedback text and "
        "uses them to adapt future agent responses in this conversation."
    ),
    responses={
        404: {"description": "Conversation or message not found"},
        422: {"description": "Validation error (e.g. rating out of range)"},
    },
)
async def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """Store feedback and extract any user preferences from the text."""
    logger.info(
        "Request: feedback conv=%s msg=%s rating=%d",
        payload.conversation_id,
        payload.message_id,
        payload.rating,
    )

    # Verify the conversation exists before calling the service
    conv_repo = ConversationRepository(db)
    if conv_repo.get_by_id(payload.conversation_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    svc = FeedbackService(db)
    try:
        fb = svc.submit_feedback(
            conversation_id=payload.conversation_id,
            message_id=payload.message_id,
            rating=payload.rating,
            feedback_text=payload.feedback_text,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return FeedbackResponse(success=True, feedback_id=fb.id)
