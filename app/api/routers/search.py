"""
Search API endpoint.

Provides unified search across cases, documents, and recommendations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database.session import get_db
from app.models.case import Case
from app.models.case_document import CaseDocument
from app.models.recommendation import Recommendation
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", status_code=status.HTTP_200_OK)
async def search(
    q: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Search across cases, documents, and recommendations.

    Args:
        q: Search query string
        db: Database session

    Returns:
        Grouped search results
    """
    if not q or len(q.strip()) < 2:
        return {"cases": [], "documents": [], "recommendations": [], "total": 0}

    query = f"%{q.strip()}%"

    # Search cases
    case_result = await db.execute(
        select(Case)
        .where(
            or_(
                Case.title.ilike(query),
                Case.case_number.ilike(query),
                Case.description.ilike(query),
                Case.client_name.ilike(query),
            )
        )
        .limit(10)
    )
    cases = case_result.scalars().all()

    # Search documents
    doc_result = await db.execute(
        select(CaseDocument)
        .where(
            or_(
                CaseDocument.title.ilike(query),
                CaseDocument.file_name.ilike(query),
                CaseDocument.description.ilike(query),
            )
        )
        .limit(10)
    )
    documents = doc_result.scalars().all()

    # Search recommendations
    rec_result = await db.execute(
        select(Recommendation)
        .where(
            or_(
                Recommendation.title.ilike(query),
                Recommendation.description.ilike(query),
                Recommendation.reasoning.ilike(query),
            )
        )
        .limit(10)
    )
    recommendations = rec_result.scalars().all()

    return {
        "cases": [
            {
                "id": c.id,
                "title": c.title,
                "case_number": c.case_number,
                "status": c.status,
                "type": "case",
            }
            for c in cases
        ],
        "documents": [
            {
                "id": d.id,
                "title": d.file_name,
                "case_id": d.case_id,
                "status": d.meta_data.get("status") if d.meta_data else "unknown",
                "type": "document",
            }
            for d in documents
        ],
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "case_id": r.case_id,
                "status": r.status,
                "priority": r.priority,
                "type": "recommendation",
            }
            for r in recommendations
        ],
        "total": len(cases) + len(documents) + len(recommendations),
    }
