from fastapi import APIRouter

from app.schemas import ReviewsResponse

router = APIRouter(prefix="/v1/content", tags=["content"])


@router.get("/reviews", response_model=ReviewsResponse, operation_id="listReviews")
async def reviews() -> ReviewsResponse:
    # Real reviews only — none stored yet, so the storefront hides the block
    # rather than shipping invented social proof (spec §J).
    return ReviewsResponse(items=[])
