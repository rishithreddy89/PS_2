"""
Enumerations for roles, permissions, and status values.
"""

from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""

    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions."""

    CASE_READ = "case:read"
    CASE_CREATE = "case:create"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"

    DOCUMENT_READ = "document:read"
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"

    RECOMMENDATION_READ = "recommendation:read"
    RECOMMENDATION_CREATE = "recommendation:create"
    RECOMMENDATION_APPROVE = "recommendation:approve"
    RECOMMENDATION_REJECT = "recommendation:reject"

    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    ADMIN_ACCESS = "admin:access"


class CaseStatus(str, Enum):
    """Case status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CasePriority(str, Enum):
    """Case priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RecommendationStatus(str, Enum):
    """Recommendation status values."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DocumentType(str, Enum):
    """Document type classifications."""

    EMAIL = "email"
    CONTRACT = "contract"
    COURT_FILING = "court_filing"
    EVIDENCE = "evidence"
    CORRESPONDENCE = "correspondence"
    LEGAL_BRIEF = "legal_brief"
    MOTION = "motion"
    DISCOVERY = "discovery"
    OTHER = "other"


class AgentStatus(str, Enum):
    """Agent registration status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class ToolStatus(str, Enum):
    """Tool registration status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class ExecutionStatus(str, Enum):
    """Planner execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
