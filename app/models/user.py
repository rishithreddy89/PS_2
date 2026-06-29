"""
User model for authentication and authorization.
"""

from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class User(Base, BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    cases = relationship("Case", back_populates="assigned_user", lazy="selectin")
    feedbacks = relationship("Feedback", back_populates="user", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
