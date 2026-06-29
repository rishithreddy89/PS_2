"""
Case Pydantic schemas for API validation.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import BaseResponse, BaseSchema


class CaseBase(BaseSchema):
    """Base case schema."""

    case_number: str = Field(..., min_length=1, max_length=100, description="Case number")
    title: str = Field(..., min_length=1, max_length=500, description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field(..., description="Case status")
    priority: str = Field(..., description="Case priority")
    case_type: str = Field(..., description="Case type")
    client_name: str = Field(..., min_length=1, max_length=255, description="Client name")
    opposing_party: Optional[str] = Field(None, max_length=255, description="Opposing party")


class CaseCreate(CaseBase):
    """Schema for creating a new case."""

    jurisdiction: Optional[str] = Field(None, max_length=100, description="Jurisdiction")
    court: Optional[str] = Field(None, max_length=255, description="Court name")
    judge_name: Optional[str] = Field(None, max_length=255, description="Judge name")
    filing_date: Optional[date] = Field(None, description="Filing date")
    next_hearing_date: Optional[date] = Field(None, description="Next hearing date")
    statute_of_limitations: Optional[date] = Field(None, description="Statute of limitations")
    estimated_value: Optional[Decimal] = Field(None, description="Estimated case value")
    assigned_user_id: Optional[str] = Field(None, description="Assigned user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Case tags")


class CaseUpdate(BaseSchema):
    """Schema for updating a case."""

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    status: Optional[str] = Field(None, description="Case status")
    priority: Optional[str] = Field(None, description="Case priority")
    case_type: Optional[str] = Field(None, description="Case type")
    client_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Client name")
    opposing_party: Optional[str] = Field(None, max_length=255, description="Opposing party")
    jurisdiction: Optional[str] = Field(None, max_length=100, description="Jurisdiction")
    court: Optional[str] = Field(None, max_length=255, description="Court name")
    judge_name: Optional[str] = Field(None, max_length=255, description="Judge name")
    filing_date: Optional[date] = Field(None, description="Filing date")
    next_hearing_date: Optional[date] = Field(None, description="Next hearing date")
    statute_of_limitations: Optional[date] = Field(None, description="Statute of limitations")
    estimated_value: Optional[Decimal] = Field(None, description="Estimated case value")
    assigned_user_id: Optional[str] = Field(None, description="Assigned user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Case tags")


class CaseResponse(CaseBase, BaseResponse):
    """Schema for case response."""

    jurisdiction: Optional[str] = None
    court: Optional[str] = None
    judge_name: Optional[str] = None
    filing_date: Optional[date] = None
    next_hearing_date: Optional[date] = None
    statute_of_limitations: Optional[date] = None
    estimated_value: Optional[Decimal] = None
    assigned_user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
