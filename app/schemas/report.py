"""
Schemas for the complete multi-agent legal analysis report.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TimelineEvent(BaseModel):
    """A chronological event extracted from documents."""
    date: str = Field(..., description="Date or timeframe of the event")
    event: str = Field(..., description="Description of what occurred")
    source_document: str = Field(..., description="Document this event was extracted from")
    importance: str = Field(..., description="High, Medium, or Low")

class EvidenceItem(BaseModel):
    """An extracted piece of evidence."""
    fact: str = Field(..., description="The factual claim")
    status: str = Field(..., description="Available or Missing")
    importance: str = Field(..., description="Critical, High, Medium, Low")
    reliability: str = Field(..., description="High, Medium, Low")
    source: str = Field(..., description="Document name or 'Not Produced'")

class Contradiction(BaseModel):
    """A detected contradiction in the evidence."""
    description: str = Field(..., description="Description of the contradiction")
    source_a: str = Field(..., description="First source")
    source_b: str = Field(..., description="Second source")
    impact: str = Field(..., description="How this impacts the case")

class RiskScores(BaseModel):
    """Numerical risk assessments."""
    litigation_risk: int = Field(..., ge=0, le=100, description="Risk of litigation (0-100)")
    evidence_strength: int = Field(..., ge=0, le=100, description="Strength of evidence (0-100)")
    urgency: int = Field(..., ge=0, le=100, description="Urgency of action (0-100)")
    settlement_probability: int = Field(..., ge=0, le=100, description="Probability of settlement (0-100)")
    employer_defense: int = Field(..., ge=0, le=100, description="Strength of employer defense (0-100)")
    explanation: str = Field(..., description="Brief reasoning for these scores")

class ApplicableLaw(BaseModel):
    """A relevant law or statute."""
    name: str = Field(..., description="Name of the law/statute")
    reason: str = Field(..., description="Why it applies")
    relevance: str = Field(..., description="High, Medium, Low")
    confidence: int = Field(..., ge=0, le=100)

class Precedent(BaseModel):
    """A relevant case precedent."""
    case_name: str
    court: str
    similarity: str = Field(..., description="High, Medium, Low")
    reason: str = Field(..., description="Why it is similar")

class LegalIssue(BaseModel):
    """Identified legal issue."""
    issue_type: str = Field(..., description="e.g., retaliation, discrimination, contract breach")
    description: str
    severity: str = Field(..., description="Critical, High, Medium, Low")

class ExecutiveSummary(BaseModel):
    """Executive summary of the case."""
    case_overview: str
    strengths: List[str]
    weaknesses: List[str]
    most_likely_legal_issues: List[str]
    most_urgent_actions: List[str]
    estimated_litigation_complexity: str
    estimated_evidence_quality: str

class FinalCaseReport(BaseModel):
    """The completely assembled case analysis report."""
    executive_summary: ExecutiveSummary
    timeline: List[TimelineEvent]
    evidence_matrix: List[EvidenceItem]
    contradictions: List[Contradiction]
    missing_evidence: List[str]
    legal_issues: List[LegalIssue]
    risk_assessment: RiskScores
    applicable_laws: List[ApplicableLaw]
    precedents: List[Precedent]
