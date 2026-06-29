"""
Memory model for storing agent memory and context.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class Memory(Base, BaseModel):
    """Memory model for storing agent memory and context."""

    __tablename__ = "memories"

    case_id = Column(CHAR(36), ForeignKey("cases.id"), nullable=True, index=True)
    execution_id = Column(CHAR(36), ForeignKey("planner_executions.id"), nullable=True, index=True)

    memory_type = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)

    ttl_seconds = Column(Integer, nullable=True)

    meta_data = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="memories")
    execution = relationship("PlannerExecution", back_populates="memories", lazy="selectin")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Memory(id={self.id}, memory_type={self.memory_type}, key={self.key})>"
