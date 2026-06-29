"""Response models for AI-powered agents."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RetrievalResponse(BaseModel):
    """Retrieval agent AI response."""
    search_queries: List[str] = Field(default_factory=list)
    document_types: List[str] = Field(default_factory=list)
    priority_sources: List[str] = Field(default_factory=list)
    reasoning: str = ""


class EvidenceAnalysis(BaseModel):
    """Evidence item analysis."""
    id: str
    description: str
    quality: str


class EvidenceResponse(BaseModel):
    """Evidence agent AI response."""
    strong_evidence: List[EvidenceAnalysis] = Field(default_factory=list)
    weak_evidence: List[EvidenceAnalysis] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    overall_strength: str = "moderate"
    reasoning: str = ""


class TimelineEventModel(BaseModel):
    """Timeline event model."""
    date: str
    description: str
    type: str
    is_deadline: bool = False
    is_urgent: bool = False


class TimelineResponse(BaseModel):
    """Timeline agent AI response."""
    events: List[TimelineEventModel] = Field(default_factory=list)
    critical_deadlines: List[str] = Field(default_factory=list)
    overdue_items: List[str] = Field(default_factory=list)


class RiskItemModel(BaseModel):
    """Risk item model."""
    risk_id: str
    type: str
    description: str
    severity: str
    probability: float
    impact: str
    mitigation: str = ""


class RiskResponse(BaseModel):
    """Risk agent AI response."""
    risks: List[RiskItemModel] = Field(default_factory=list)
    overall_risk_level: str = "medium"
    risk_score: float = 50.0
