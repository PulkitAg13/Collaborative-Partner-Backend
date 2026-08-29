"""Health check route."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns OK when the API is running.",
    response_description="Service status",
)
async def health_check() -> dict[str, str]:
    """Simple liveness probe — useful for Docker/Cloud Run health checks."""
    return {"status": "ok"}
