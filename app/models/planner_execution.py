"""
Planner execution model for tracking agent orchestration.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class PlannerExecution(Base, BaseModel):
    """Planner execution model for tracking agent workflows."""

    __tablename__ = "planner_executions"

    case_id = Column(CHAR(36), ForeignKey("cases.id"), nullable=True, index=True)

    status = Column(String(50), nullable=False, default="pending")
    execution_type = Column(String(100), nullable=False)

    input_data = Column(JSON, nullable=False)
    execution_plan = Column(JSON, nullable=True)
    agent_outputs = Column(JSON, nullable=True)
    final_output = Column(JSON, nullable=True)

    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    meta_data = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="planner_executions", lazy="selectin")
    recommendations = relationship("Recommendation", back_populates="execution", lazy="selectin", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="execution", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<PlannerExecution(id={self.id}, status={self.status}, execution_type={self.execution_type})>"
