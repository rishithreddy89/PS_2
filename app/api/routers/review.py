"""
Review and feedback API endpoints.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.recommendation import Recommendation
from app.models.feedback import Feedback
from app.services.workflow import WorkflowExecutionService
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/review", tags=["Review"])


class ReviewRequest(BaseModel):
    decision: str  # approved, rejected, modified
    comments: Optional[str] = None
    modified_content: Optional[dict] = None
    reviewer_id: Optional[str] = None


@router.post("/recommendations/{recommendation_id}/review")
async def submit_review(
    recommendation_id: str,
    review: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit review for a recommendation."""
    # Get recommendation
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id)
    )
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    # Ensure a user with id "current-user" exists to satisfy foreign key constraint
    from app.models.user import User
    reviewer_id = review.reviewer_id or "current-user"
    reviewer = await db.get(User, reviewer_id)
    if not reviewer:
        # Create a default reviewer user if not present
        reviewer = User(
            id=reviewer_id,
            email=f"{reviewer_id}@lexmind.ai",
            hashed_password="placeholder-password-hash",
            full_name="Current Reviewer",
            role="reviewer",
            is_active=True
        )
        db.add(reviewer)
        await db.flush()

    # Create feedback record mapping to valid Feedback columns
    feedback = Feedback(
        recommendation_id=recommendation_id,
        user_id=reviewer_id,
        action_taken=review.decision,
        rating=5 if review.decision == "approved" else 1,
        comments=review.comments,
        modified_recommendation=review.modified_content,
        meta_data={
            "original_content": {
                "title": recommendation.title,
                "description": recommendation.description,
                "reasoning": recommendation.reasoning,
                "priority": recommendation.priority,
            }
        }
    )
    db.add(feedback)
    
    # Update recommendation status and metadata
    recommendation.meta_data = recommendation.meta_data or {}
    recommendation.meta_data["review_status"] = review.decision
    recommendation.meta_data["reviewed_at"] = feedback.created_at.isoformat() if feedback.created_at else None

    # Apply decision updates
    if review.decision == "approved":
        recommendation.status = "APPROVED"
    elif review.decision == "rejected":
        recommendation.status = "REJECTED"
    elif review.decision == "modified":
        recommendation.status = "APPROVED"  # modified recommendations are approved as modified
        if review.modified_content:
            if "title" in review.modified_content:
                recommendation.title = str(review.modified_content["title"])
            if "description" in review.modified_content:
                recommendation.description = str(review.modified_content["description"])
            if "reasoning" in review.modified_content:
                recommendation.reasoning = str(review.modified_content["reasoning"])
            if "priority" in review.modified_content:
                recommendation.priority = str(review.modified_content["priority"])

    await db.commit()
    
    # Update memory
    workflow_service = WorkflowExecutionService(db)
    await workflow_service.process_feedback_and_update_memory(
        recommendation_id=recommendation_id,
        feedback={
            "decision": review.decision,
            "comments": review.comments,
            "modified_content": review.modified_content,
        },
        case_id=recommendation.case_id
    )
    
    return {
        "feedback_id": feedback.id,
        "status": "success",
        "message": f"Review {review.decision} submitted successfully"
    }


@router.get("/recommendations/{recommendation_id}/reviews")
async def get_reviews(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews for a recommendation."""
    result = await db.execute(
        select(Feedback).where(Feedback.recommendation_id == recommendation_id)
    )
    feedbacks = result.scalars().all()
    
    return {
        "reviews": [
            {
                "id": fb.id,
                "decision": fb.feedback_type,
                "rating": fb.rating,
                "comments": fb.comments,
                "reviewer_id": fb.user_id,
                "created_at": fb.created_at.isoformat(),
            }
            for fb in feedbacks
        ]
    }
