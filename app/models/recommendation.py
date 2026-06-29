"""
Recommendation model for Next Best Action recommendations.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Float
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class Recommendation(Base, BaseModel):
    """Recommendation model for Next Best Action suggestions."""

    __tablename__ = "recommendations"

    case_id = Column(CHAR(36), ForeignKey("cases.id"), nullable=False, index=True)
    execution_id = Column(CHAR(36), ForeignKey("planner_executions.id"), nullable=True, index=True)

    action_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)

    reasoning = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)

    priority = Column(String(50), nullable=False, default="medium")
    status = Column(String(50), nullable=False, default="pending")

    supporting_evidence = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)
    justification = Column(JSON, nullable=True)
    missing_evidence = Column(JSON, nullable=True)
    applicable_laws = Column(JSON, nullable=True)
    detailed_applicable_laws = Column(JSON, nullable=True)
    relevant_precedents = Column(JSON, nullable=True)
    detailed_precedents = Column(JSON, nullable=True)
    legal_risks = Column(JSON, nullable=True)
    counterarguments = Column(JSON, nullable=True)
    alternative_strategies = Column(JSON, nullable=True)
    next_best_actions = Column(JSON, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    urgency = Column(String(100), nullable=True)
    priority_explanation = Column(Text, nullable=True)
    confidence_explanation = Column(Text, nullable=True)
    risk_assessment = Column(JSON, nullable=True)
    timeline = Column(JSON, nullable=True)
    validation = Column(JSON, nullable=True)
    contradictions = Column(JSON, nullable=True)
    executive_opinion = Column(JSON, nullable=True)
    
    meta_data = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="recommendations")
    execution = relationship("PlannerExecution", back_populates="recommendations")
    feedbacks = relationship("Feedback", back_populates="recommendation", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Recommendation(id={self.id}, action_type={self.action_type}, status={self.status})>"
