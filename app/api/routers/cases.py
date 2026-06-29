"""
Case management API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.schemas.base import PaginatedResponse, PaginationParams
from app.services.case import CaseService

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db),
) -> CaseResponse:
    """
    Create a new case and automatically trigger workflow.

    Args:
        case_data: Case creation data
        db: Database session

    Returns:
        Created case with execution_id in metadata
    """
    from app.services.workflow import WorkflowExecutionService
    
    service = CaseService(db)
    try:
        case = await service.create(case_data.model_dump(exclude_unset=True))
    except IntegrityError as e:
        if "Duplicate entry" in str(e.orig) and "case_number" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Case number '{case_data.case_number}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database constraint violation",
        )
    
    # Auto-trigger workflow
    workflow_service = WorkflowExecutionService(db)
    execution_id = await workflow_service.trigger_workflow_on_case_creation(
        case_id=case.id,
        case_data=case_data.model_dump(exclude_unset=True),
    )
    
    # Create response with proper metadata
    response_dict = {
        "id": case.id,
        "title": case.title,
        "case_type": case.case_type,
        "case_number": case.case_number,
        "status": case.status,
        "priority": case.priority,
        "description": case.description,
        "client_name": case.client_name,
        "opposing_party": case.opposing_party,
        "jurisdiction": case.jurisdiction,
        "court": case.court,
        "judge_name": case.judge_name,
        "filing_date": case.filing_date,
        "next_hearing_date": case.next_hearing_date,
        "statute_of_limitations": case.statute_of_limitations,
        "estimated_value": case.estimated_value,
        "meta_data": {
            "execution_id": execution_id,
            "stream_url": f"/api/v1/stream/workflow/{case.id}",
            **(case.meta_data or {})
        },
        "tags": case.tags,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }
    
    return CaseResponse(**response_dict)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> CaseResponse:
    """
    Get a case by ID.

    Args:
        case_id: Case ID
        db: Database session

    Returns:
        Case details

    Raises:
        HTTPException: If case not found
    """
    service = CaseService(db)
    case = await service.get_by_id(case_id)

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case not found: {case_id}",
        )

    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        status=case.status,
        priority=case.priority,
        case_type=case.case_type,
        client_name=case.client_name,
        opposing_party=case.opposing_party,
        jurisdiction=case.jurisdiction,
        court=case.court,
        judge_name=case.judge_name,
        filing_date=case.filing_date,
        next_hearing_date=case.next_hearing_date,
        statute_of_limitations=case.statute_of_limitations,
        estimated_value=case.estimated_value,
        assigned_user_id=case.assigned_user_id,
        metadata=case.meta_data,
        tags=case.tags,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.get("", response_model=PaginatedResponse)
async def list_cases(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """
    List all cases with pagination.

    Args:
        pagination: Pagination parameters
        db: Database session

    Returns:
        Paginated case list
    """
    service = CaseService(db)

    skip = (pagination.page - 1) * pagination.page_size
    cases = await service.get_multi(skip=skip, limit=pagination.page_size)
    total = await service.count()

    return PaginatedResponse(
        items=[
            CaseResponse(
                id=case.id,
                case_number=case.case_number,
                title=case.title,
                description=case.description,
                status=case.status,
                priority=case.priority,
                case_type=case.case_type,
                client_name=case.client_name,
                opposing_party=case.opposing_party,
                jurisdiction=case.jurisdiction,
                court=case.court,
                judge_name=case.judge_name,
                filing_date=case.filing_date,
                next_hearing_date=case.next_hearing_date,
                statute_of_limitations=case.statute_of_limitations,
                estimated_value=case.estimated_value,
                assigned_user_id=case.assigned_user_id,
                metadata=case.meta_data,
                tags=case.tags,
                created_at=case.created_at,
                updated_at=case.updated_at,
            )
            for case in cases
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
) -> CaseResponse:
    """
    Update a case.

    Args:
        case_id: Case ID
        case_data: Update data
        db: Database session

    Returns:
        Updated case

    Raises:
        HTTPException: If case not found
    """
    service = CaseService(db)
    case = await service.update(case_id, case_data.model_dump(exclude_unset=True))

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case not found: {case_id}",
        )

    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        status=case.status,
        priority=case.priority,
        case_type=case.case_type,
        client_name=case.client_name,
        opposing_party=case.opposing_party,
        jurisdiction=case.jurisdiction,
        court=case.court,
        judge_name=case.judge_name,
        filing_date=case.filing_date,
        next_hearing_date=case.next_hearing_date,
        statute_of_limitations=case.statute_of_limitations,
        estimated_value=case.estimated_value,
        assigned_user_id=case.assigned_user_id,
        metadata=case.meta_data,
        tags=case.tags,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a case.

    Args:
        case_id: Case ID
        db: Database session

    Raises:
        HTTPException: If case not found
    """
    service = CaseService(db)
    deleted = await service.delete(case_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case not found: {case_id}",
        )
