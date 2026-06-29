"""
Audit log model for tracking all system actions.
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class AuditLog(Base, BaseModel):
    """Audit log model for tracking system actions."""

    __tablename__ = "audit_logs"

    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(CHAR(36), nullable=True, index=True)

    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    changes = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type={self.entity_type})>"
