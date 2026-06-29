"""
Feedback Pydantic schemas for API validation.
"""

from typing import Any, Dict, Optional

from pydantic import Field

from app.schemas.base import BaseResponse, BaseSchema


class FeedbackBase(BaseSchema):
    """Base feedback schema."""

    recommendation_id: str = Field(..., description="Recommendation ID")
    action_taken: str = Field(..., min_length=1, max_length=50, description="Action taken")


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback."""

    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    comments: Optional[str] = Field(None, description="Feedback comments")
    modified_recommendation: Optional[Dict[str, Any]] = Field(None, description="Modified recommendation")
    outcome: Optional[str] = Field(None, max_length=100, description="Outcome")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FeedbackUpdate(BaseSchema):
    """Schema for updating feedback."""

    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    comments: Optional[str] = Field(None, description="Feedback comments")
    outcome: Optional[str] = Field(None, max_length=100, description="Outcome")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FeedbackResponse(FeedbackBase, BaseResponse):
    """Schema for feedback response."""

    user_id: str
    rating: Optional[int] = None
    comments: Optional[str] = None
    modified_recommendation: Optional[Dict[str, Any]] = None
    outcome: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
