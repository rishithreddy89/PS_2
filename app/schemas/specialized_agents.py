"""
Response models for specialized agents.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentCategory(str, Enum):
    """Document categories."""
    EMAIL = "email"
    CONTRACT = "contract"
    COURT_NOTICE = "court_notice"
    WITNESS_STATEMENT = "witness_statement"
    EVIDENCE = "evidence"
    MEETING_NOTES = "meeting_notes"
    CASE_NOTES = "case_notes"
    PDF = "pdf"
    TEXT = "text"
    OTHER = "other"


class SearchIntent(str, Enum):
    """Search intent types."""
    LEGAL_RESEARCH = "legal_research"
    PRECEDENT_SEARCH = "precedent_search"
    STATUTE_LOOKUP = "statute_lookup"
    CASE_HISTORY = "case_history"
    INTERNAL_DOCS = "internal_docs"
    PLAYBOOK = "playbook"


class EvidenceQuality(str, Enum):
    """Evidence quality assessment."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INSUFFICIENT = "insufficient"


class EntityType(str, Enum):
    """Entity types."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    AMOUNT = "amount"


# ============================================================================
# INGEST AGENT MODELS
# ============================================================================

class Entity(BaseModel):
    """Extracted entity."""
    entity_type: EntityType
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    context: Optional[str] = None


class Event(BaseModel):
    """Extracted event."""
    description: str
    date: Optional[datetime] = None
    participants: List[str] = Field(default_factory=list)
    location: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Document metadata."""
    document_id: str
    title: Optional[str] = None
    category: DocumentCategory
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None


class DocumentSummary(BaseModel):
    """Ingested document summary."""
    document_id: str
    title: str
    category: DocumentCategory
    case_type: Optional[str] = None
    entities: List[Entity] = Field(default_factory=list)
    people: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    dates: List[datetime] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    metadata: DocumentMetadata
    content_summary: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# RETRIEVAL AGENT MODELS
# ============================================================================

class SearchSource(BaseModel):
    """Search source definition."""
    source_type: str
    priority: int = Field(ge=1, le=10, default=5)
    filters: Dict[str, Any] = Field(default_factory=dict)


class RetrievalRequest(BaseModel):
    """Structured retrieval request."""
    query: str
    intent: SearchIntent
    categories: List[str] = Field(default_factory=list)
    sources: List[SearchSource] = Field(default_factory=list)
    priority: int = Field(ge=1, le=10, default=5)
    max_results: int = Field(default=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# EVIDENCE AGENT MODELS
# ============================================================================

class EvidenceItem(BaseModel):
    """Single evidence item."""
    evidence_id: str
    description: str
    quality: EvidenceQuality
    source: Optional[str] = None
    date_collected: Optional[datetime] = None


class EvidenceIssue(BaseModel):
    """Evidence issue or gap."""
    issue_type: str
    description: str
    severity: RiskLevel
    affected_evidence: List[str] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    """Evidence analysis summary."""
    total_evidence_count: int
    strong_evidence: List[EvidenceItem] = Field(default_factory=list)
    weak_evidence: List[EvidenceItem] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    duplicate_evidence: List[str] = Field(default_factory=list)
    conflicting_evidence: List[EvidenceIssue] = Field(default_factory=list)
    issues: List[EvidenceIssue] = Field(default_factory=list)
    overall_strength: EvidenceQuality
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# TIMELINE AGENT MODELS
# ============================================================================

class TimelineEvent(BaseModel):
    """Timeline event."""
    event_id: str
    description: str
    event_date: datetime
    event_type: str
    is_deadline: bool = False
    is_overdue: bool = False
    is_urgent: bool = False
    participants: List[str] = Field(default_factory=list)
    related_documents: List[str] = Field(default_factory=list)


class TimelineSummary(BaseModel):
    """Timeline summary."""
    events: List[TimelineEvent] = Field(default_factory=list)
    deadlines: List[TimelineEvent] = Field(default_factory=list)
    overdue_events: List[TimelineEvent] = Field(default_factory=list)
    urgent_events: List[TimelineEvent] = Field(default_factory=list)
    milestones: List[TimelineEvent] = Field(default_factory=list)
    earliest_date: Optional[datetime] = None
    latest_date: Optional[datetime] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# RISK AGENT MODELS
# ============================================================================

class RiskItem(BaseModel):
    """Single risk item."""
    risk_id: str
    risk_type: str
    description: str
    severity: RiskLevel
    probability: float = Field(ge=0.0, le=1.0)
    impact: str
    mitigation: Optional[str] = None
    related_items: List[str] = Field(default_factory=list)


class RiskSummary(BaseModel):
    """Risk analysis summary."""
    total_risks: int
    critical_risks: List[RiskItem] = Field(default_factory=list)
    high_risks: List[RiskItem] = Field(default_factory=list)
    medium_risks: List[RiskItem] = Field(default_factory=list)
    low_risks: List[RiskItem] = Field(default_factory=list)
    overall_risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=100.0)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# MEMORY AGENT MODELS
# ============================================================================

class MemoryContext(BaseModel):
    """Memory context for agents."""
    case_id: Optional[str] = None
    execution_id: Optional[str] = None
    short_term: Dict[str, Any] = Field(default_factory=dict)
    long_term: Dict[str, Any] = Field(default_factory=dict)
    conversation: List[Dict[str, Any]] = Field(default_factory=list)
    case_specific: Dict[str, Any] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# COMMON AGENT OUTPUT
# ============================================================================

class AgentOutput(BaseModel):
    """Generic agent output wrapper."""
    agent_id: str
    agent_name: str
    output_type: str
    data: Dict[str, Any]
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
