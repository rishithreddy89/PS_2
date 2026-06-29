"""
Schemas for Next Best Action (NBA) and Decision Intelligence Layer.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class AlternativeAction(BaseModel):
    """Alternative action option."""
    action: str
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class EvidenceCitation(BaseModel):
    """Evidence traceability citation."""
    document: str
    section: Optional[str] = None
    page: Optional[str] = None
    chunk_id: Optional[str] = None
    retrieval_score: float = Field(ge=0.0, le=1.0)
    strength: str
    quote: str


class RecommendationJustification(BaseModel):
    """Detailed justification for a recommendation."""
    why_appropriate: str
    why_now: str
    supporting_facts: List[str] = Field(default_factory=list)
    weakening_facts: List[str] = Field(default_factory=list)
    required_assumptions: List[str] = Field(default_factory=list)


class Counterargument(BaseModel):
    """Likely opposing counsel argument."""
    argument: str
    strength: str
    likelihood_of_success: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)


class DetailedAlternativeStrategy(BaseModel):
    """Rich alternative strategy."""
    strategy: str
    advantages: List[str] = Field(default_factory=list)
    disadvantages: List[str] = Field(default_factory=list)
    estimated_success: str
    when_to_choose: str
    trade_offs: str


class ActionPlanStep(BaseModel):
    """Chronological litigation step."""
    timing: str
    action: str


class DetailedApplicableLaw(BaseModel):
    """Detailed applicable law analysis."""
    statute: str
    section: str
    chunk_id: str
    source_document: str
    retrieval_score: float = Field(ge=0.0, le=1.0)
    why_it_applies: str


class DetailedPrecedent(BaseModel):
    """Detailed precedent retrieval."""
    case_name: str
    court: str
    year: str
    chunk_id: str
    retrieval_score: float = Field(ge=0.0, le=1.0)


class ContradictionAnalysis(BaseModel):
    """Legal contradiction analysis."""
    employer_claim: str
    evidence: str
    legal_significance: str


class ExecutiveLegalOpinion(BaseModel):
    """Senior attorney executive opinion."""
    overall_assessment: str
    case_strength: str
    primary_claim: str
    strongest_evidence: str
    weakest_evidence: str
    primary_recommendation: str
    biggest_litigation_risk: str
    overall_confidence: str


class NextBestAction(BaseModel):
    """Single Next Best Action recommendation."""
    title: str
    priority: str  # urgent, high, medium, low
    priority_explanation: str = Field(default="")
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_explanation: str = Field(default="")
    evidence_completeness_score: str = Field(default="")
    executive_summary: str
    reasoning: str
    justification: Optional[RecommendationJustification] = None
    supporting_evidence: List[EvidenceCitation] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    applicable_laws: List[str] = Field(default_factory=list)
    detailed_applicable_laws: List[DetailedApplicableLaw] = Field(default_factory=list)
    relevant_precedents: List[str] = Field(default_factory=list)
    detailed_precedents: List[DetailedPrecedent] = Field(default_factory=list)
    next_best_actions: List[str] = Field(default_factory=list)
    alternative_strategies: List[DetailedAlternativeStrategy] = Field(default_factory=list)
    counterarguments: List[Counterargument] = Field(default_factory=list)
    expected_outcome: str
    urgency: str
    source_citations: List[str] = Field(default_factory=list)
    rank: int = Field(default=1, ge=1, le=3)

    @model_validator(mode="after")
    def validate_no_empty_fields(self) -> "NextBestAction":
        def is_empty(val: Any) -> bool:
            if isinstance(val, str) and not val.strip():
                return True
            if isinstance(val, (list, dict)) and not val:
                return True
            return False

        for field_name, field_value in self:
            if field_name == "rank":
                continue
            if is_empty(field_value):
                # We raise a ValueError so OpenRouter Pydantic validation kicks in and retries
                raise ValueError(
                    f"Field '{field_name}' is empty. You must fully populate every field. "
                    f"No empty strings, arrays, or objects allowed. "
                    f"If data is genuinely unavailable, return a structured explanation "
                    f"for arrays/objects (e.g. [{{\"status\": \"not_available\", \"reason\": \"...\"}}]), "
                    f"or a descriptive text explanation for strings."
                )
        return self


class NBAResponse(BaseModel):
    """NBA Agent response with top 3 recommendations."""
    executive_opinion: Optional[ExecutiveLegalOpinion] = None
    action_plan: List[ActionPlanStep] = Field(default_factory=list)
    contradiction_analysis: List[ContradictionAnalysis] = Field(default_factory=list)
    recommendations: List[NextBestAction] = Field(max_length=3)
    overall_strategy: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_complete_response(self) -> "NBAResponse":
        has_insufficient = "insufficient evidence" in (self.overall_strategy or "").lower()
        
        if not self.recommendations and not has_insufficient:
            raise ValueError("LLM returned no recommendations. You must provide at least one recommendation unless there is explicitly insufficient evidence.")
            
        if self.executive_opinion is None:
            raise ValueError("executive_opinion is a required field and cannot be null.")
            
        if not self.action_plan:
            raise ValueError("action_plan must contain at least one step.")
            
        if not self.contradiction_analysis:
            raise ValueError("contradiction_analysis must not be empty. If none exist, document that explicitly.")
            
        return self

class EvidenceCheck(BaseModel):
    """Evidence support check."""
    has_support: bool
    evidence_quality: str  # strong, moderate, weak
    missing_evidence: List[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Evaluation result for a recommendation."""
    recommendation_rank: int
    evidence_support_score: float = Field(ge=0.0, le=1.0)
    citation_quality_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)
    confidence_calibration: str  # well_calibrated, overconfident, underconfident
    evidence_check: EvidenceCheck
    potential_issues: List[str] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=1.0)
    passed: bool


class EvaluationResponse(BaseModel):
    """Evaluation Agent response."""
    evaluations: List[EvaluationResult]
    all_passed: bool
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    recommendations_text: str = ""


class ReflectionImprovement(BaseModel):
    """Suggested improvement for a recommendation."""
    aspect: str  # reasoning, confidence, priority, evidence, alternatives
    current_value: str
    suggested_value: str
    justification: str


class ReflectionResult(BaseModel):
    """Reflection result for a recommendation."""
    recommendation_rank: int
    needs_improvement: bool
    improvements: List[ReflectionImprovement] = Field(default_factory=list)
    approval_status: str  # approved, needs_revision


class ReflectionResponse(BaseModel):
    """Reflection Agent response."""
    reflections: List[ReflectionResult]
    revised_recommendations: Optional[List[NextBestAction]] = None
    approved: bool


class ExplanationDetail(BaseModel):
    """Detailed explanation component."""
    why_this_action: str
    why_now: str
    supporting_laws: List[str] = Field(default_factory=list)
    supporting_precedents: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence_explanation: str
    alternatives_considered: List[str] = Field(default_factory=list)
    risk_if_ignored: str


class ExplainabilityResponse(BaseModel):
    """Explainability Agent response."""
    explanations: List[ExplanationDetail]


class HumanReviewDecision(BaseModel):
    """Human review decision."""
    recommendation_rank: int
    decision: str  # approved, rejected, modified
    comments: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class HumanReviewRequest(BaseModel):
    """Human review request."""
    case_id: str
    recommendations: List[NextBestAction]
    explanations: List[ExplanationDetail]


class HumanReviewResponse(BaseModel):
    """Human review preparation response."""
    case_id: str
    recommendations_count: int
    requires_approval: bool
    prepared_for_review: bool
    review_context: Dict[str, Any] = Field(default_factory=dict)


class FeedbackCreate(BaseModel):
    """Feedback submission schema."""
    recommendation_id: str
    user_id: str
    decision: str  # approved, rejected, modified
    rating: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


from app.schemas.report import (
    ExecutiveSummary,
    TimelineEvent,
    EvidenceItem,
    Contradiction,
    RiskScores,
    ApplicableLaw,
    Precedent,
    LegalIssue
)

class AnalysisRequest(BaseModel):
    """Full analysis request."""
    case_id: str
    query: Optional[str] = None
    include_memory: bool = True

class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    case_id: str
    execution_id: str
    recommendations: List[NextBestAction]
    executive_summary: Optional[ExecutiveSummary] = None
    timeline: List[TimelineEvent] = Field(default_factory=list)
    evidence_matrix: List[EvidenceItem] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    legal_issues: List[LegalIssue] = Field(default_factory=list)
    risk_assessment: Optional[RiskScores] = None
    applicable_laws: List[ApplicableLaw] = Field(default_factory=list)
    precedents: List[Precedent] = Field(default_factory=list)
    evaluations: List[EvaluationResult] = Field(default_factory=list)
    explanations: List[ExplanationDetail] = Field(default_factory=list)
    overall_quality: float = 0.0
    requires_review: bool = True
    generated_at: datetime = Field(default_factory=datetime.utcnow)
