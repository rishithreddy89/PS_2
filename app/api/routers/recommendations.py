"""
Recommendation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.recommendation import RecommendationCreate, RecommendationResponse, RecommendationUpdate
from app.schemas.base import PaginatedResponse, PaginationParams
from app.services.recommendation import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    recommendation_data: RecommendationCreate,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Create a new recommendation.

    Args:
        recommendation_data: Recommendation creation data
        db: Database session

    Returns:
        Created recommendation
    """
    service = RecommendationService(db)
    recommendation = await service.create(recommendation_data.model_dump(exclude_unset=True))
    return RecommendationResponse.model_validate(recommendation)


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Get a recommendation by ID.

    Args:
        recommendation_id: Recommendation ID
        db: Database session

    Returns:
        Recommendation details

    Raises:
        HTTPException: If recommendation not found
    """
    service = RecommendationService(db)
    recommendation = await service.get_by_id(recommendation_id)

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation not found: {recommendation_id}",
        )

    return RecommendationResponse.model_validate(recommendation)


@router.get("", response_model=PaginatedResponse)
async def list_recommendations(
    case_id: str = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """
    List recommendations with optional case filter.

    Args:
        case_id: Optional case ID filter
        pagination: Pagination parameters
        db: Database session

    Returns:
        Paginated recommendation list
    """
    service = RecommendationService(db)

    filters = {"case_id": case_id} if case_id else None
    skip = (pagination.page - 1) * pagination.page_size
    recommendations = await service.get_multi(skip=skip, limit=pagination.page_size, filters=filters)
    total = await service.count(filters)

    return PaginatedResponse(
        items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: str,
    recommendation_data: RecommendationUpdate,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Update a recommendation.

    Args:
        recommendation_id: Recommendation ID
        recommendation_data: Update data
        db: Database session

    Returns:
        Updated recommendation

    Raises:
        HTTPException: If recommendation not found
    """
    service = RecommendationService(db)
    recommendation = await service.update(
        recommendation_id, recommendation_data.model_dump(exclude_unset=True)
    )

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation not found: {recommendation_id}",
        )

    return RecommendationResponse.model_validate(recommendation)
