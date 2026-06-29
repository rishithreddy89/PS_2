"""
Recommendation Pydantic schemas for API validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from app.schemas.base import BaseResponse, BaseSchema


class RecommendationBase(BaseSchema):
    """Base recommendation schema."""

    case_id: str = Field(..., description="Case ID")
    action_type: str = Field(..., min_length=1, max_length=100, description="Action type")
    title: str = Field(..., min_length=1, max_length=500, description="Recommendation title")
    description: str = Field(..., min_length=1, description="Recommendation description")
    reasoning: str = Field(..., min_length=1, description="Reasoning for recommendation")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    priority: str = Field(..., description="Priority level")


class RecommendationCreate(RecommendationBase):
    """Schema for creating a new recommendation."""

    execution_id: Optional[str] = Field(None, description="Planner execution ID")
    supporting_evidence: Optional[List[Any]] = Field(None, description="Supporting evidence")
    executive_summary: Optional[str] = Field(None)
    justification: Optional[Dict[str, Any]] = Field(None)
    missing_evidence: Optional[List[Any]] = Field(None)
    applicable_laws: Optional[List[Any]] = Field(None)
    detailed_applicable_laws: Optional[List[Any]] = Field(None)
    relevant_precedents: Optional[List[Any]] = Field(None)
    detailed_precedents: Optional[List[Any]] = Field(None)
    legal_risks: Optional[List[Any]] = Field(None)
    counterarguments: Optional[List[Any]] = Field(None)
    alternative_strategies: Optional[List[Any]] = Field(None)
    next_best_actions: Optional[List[Any]] = Field(None)
    expected_outcome: Optional[str] = Field(None)
    urgency: Optional[str] = Field(None)
    priority_explanation: Optional[str] = Field(None)
    confidence_explanation: Optional[str] = Field(None)
    risk_assessment: Optional[Dict[str, Any]] = Field(None)
    timeline: Optional[List[Any]] = Field(None)
    validation: Optional[Dict[str, Any]] = Field(None)
    contradictions: Optional[List[Any]] = Field(None)
    executive_opinion: Optional[Dict[str, Any]] = Field(None)
    
    # Accept both "metadata" (API) and "meta_data" (ORM column name)
    meta_data: Optional[Dict[str, Any]] = Field(None, alias="meta_data", description="Additional metadata")

    class Config:
        populate_by_name = True


class RecommendationUpdate(BaseSchema):
    """Schema for updating a recommendation."""

    title: Optional[str] = Field(None, description="Recommendation title")
    description: Optional[str] = Field(None, description="Recommendation description")
    reasoning: Optional[str] = Field(None, description="Reasoning for recommendation")
    status: Optional[str] = Field(None, description="Recommendation status")
    priority: Optional[str] = Field(None, description="Priority level")
    supporting_evidence: Optional[List[Any]] = Field(None, description="Supporting evidence")
    executive_summary: Optional[str] = Field(None)
    justification: Optional[Dict[str, Any]] = Field(None)
    missing_evidence: Optional[List[Any]] = Field(None)
    applicable_laws: Optional[List[Any]] = Field(None)
    detailed_applicable_laws: Optional[List[Any]] = Field(None)
    relevant_precedents: Optional[List[Any]] = Field(None)
    detailed_precedents: Optional[List[Any]] = Field(None)
    legal_risks: Optional[List[Any]] = Field(None)
    counterarguments: Optional[List[Any]] = Field(None)
    alternative_strategies: Optional[List[Any]] = Field(None)
    next_best_actions: Optional[List[Any]] = Field(None)
    expected_outcome: Optional[str] = Field(None)
    urgency: Optional[str] = Field(None)
    priority_explanation: Optional[str] = Field(None)
    confidence_explanation: Optional[str] = Field(None)
    risk_assessment: Optional[Dict[str, Any]] = Field(None)
    timeline: Optional[List[Any]] = Field(None)
    validation: Optional[Dict[str, Any]] = Field(None)
    contradictions: Optional[List[Any]] = Field(None)
    executive_opinion: Optional[Dict[str, Any]] = Field(None)
    meta_data: Optional[Dict[str, Any]] = Field(None, alias="meta_data", description="Additional metadata")

    class Config:
        populate_by_name = True


class RecommendationResponse(RecommendationBase, BaseResponse):
    """Schema for recommendation response."""

    execution_id: Optional[str] = None
    status: str
    
    # Required default non-null fields for frontend safety
    supporting_evidence: List[Any] = Field(default_factory=list)
    executive_summary: str = Field(default="")
    justification: Dict[str, Any] = Field(default_factory=dict)
    missing_evidence: List[Any] = Field(default_factory=list)
    applicable_laws: List[Any] = Field(default_factory=list)
    detailed_applicable_laws: List[Any] = Field(default_factory=list)
    relevant_precedents: List[Any] = Field(default_factory=list)
    detailed_precedents: List[Any] = Field(default_factory=list)
    legal_risks: List[Any] = Field(default_factory=list)
    counterarguments: List[Any] = Field(default_factory=list)
    alternative_strategies: List[Any] = Field(default_factory=list)
    next_best_actions: List[Any] = Field(default_factory=list)
    expected_outcome: str = Field(default="")
    urgency: str = Field(default="")
    priority_explanation: str = Field(default="")
    confidence_explanation: str = Field(default="")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    timeline: List[Any] = Field(default_factory=list)
    validation: Dict[str, Any] = Field(default_factory=dict)
    contradictions: List[Any] = Field(default_factory=list)
    executive_opinion: Dict[str, Any] = Field(default_factory=dict)
    
    # Map ORM column meta_data → response field meta_data (expose as meta_data)
    meta_data: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="before")
    @classmethod
    def ensure_defaults(cls, data: Any) -> Any:
        # Pydantic v2 mode="before" runs before validation.
        # It receives either a dict or the ORM object (because of from_attributes=True)
        if isinstance(data, dict):
            d = data.copy()
        else:
            d = {}
            # Safely extract attributes if it's an ORM model
            for field_name in cls.model_fields.keys():
                d[field_name] = getattr(data, field_name, None)

        arrays = [
            "supporting_evidence", "missing_evidence", "applicable_laws", 
            "detailed_applicable_laws", "relevant_precedents", "detailed_precedents", 
            "legal_risks", "counterarguments", "alternative_strategies", 
            "next_best_actions", "timeline", "contradictions"
        ]
        dicts = [
            "justification", "risk_assessment", "validation", "executive_opinion", "meta_data"
        ]
        strings = [
            "executive_summary", "expected_outcome", "urgency", 
            "priority_explanation", "confidence_explanation"
        ]

        for field in arrays:
            if not d.get(field):
                d[field] = [{"status": "not_available", "reason": f"No data was generated for {field}."}]
        for field in dicts:
            if not d.get(field):
                d[field] = {"status": "not_available", "reason": f"No data was generated for {field}."}
        for field in strings:
            if not d.get(field):
                d[field] = f"Not available: No data was generated for {field}."
                
        # Fix up supporting_evidence if it accidentally contains {"items": [...]} or is just {}
        ev = d.get("supporting_evidence")
        if isinstance(ev, dict) and "items" in ev:
            d["supporting_evidence"] = ev["items"] if isinstance(ev["items"], list) else [{"status": "not_available", "reason": "No data was generated for supporting_evidence."}]
        elif not isinstance(ev, list) or not ev:
            d["supporting_evidence"] = [{"status": "not_available", "reason": "No data was generated for supporting_evidence."}]

        return d

