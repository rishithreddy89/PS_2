"""
Case model for legal case management.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Date, Numeric
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class Case(Base, BaseModel):
    """Case model for legal case management."""

    __tablename__ = "cases"

    case_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="open")
    priority = Column(String(50), nullable=False, default="medium")
    case_type = Column(String(100), nullable=False)

    client_name = Column(String(255), nullable=False)
    opposing_party = Column(String(255), nullable=True)

    jurisdiction = Column(String(100), nullable=True)
    court = Column(String(255), nullable=True)
    judge_name = Column(String(255), nullable=True)

    filing_date = Column(Date, nullable=True)
    next_hearing_date = Column(Date, nullable=True)
    statute_of_limitations = Column(Date, nullable=True)

    estimated_value = Column(Numeric(15, 2), nullable=True)
    
    assigned_user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True)

    meta_data = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    assigned_user = relationship("User", back_populates="cases", lazy="selectin")
    documents = relationship("CaseDocument", back_populates="case", lazy="selectin", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="case", lazy="selectin", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="case", lazy="selectin", cascade="all, delete-orphan")
    planner_executions = relationship("PlannerExecution", back_populates="case", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Case(id={self.id}, case_number={self.case_number}, status={self.status})>"
