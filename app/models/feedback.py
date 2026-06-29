"""
Feedback model for capturing human feedback on recommendations.
"""

from sqlalchemy import Column, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import relationship

from app.database.base import BaseModel
from app.database.session import Base


class Feedback(Base, BaseModel):
    """Feedback model for human-in-the-loop learning."""

    __tablename__ = "feedbacks"

    recommendation_id = Column(CHAR(36), ForeignKey("recommendations.id"), nullable=False, index=True)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)

    action_taken = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=True)
    comments = Column(Text, nullable=True)

    modified_recommendation = Column(JSON, nullable=True)
    outcome = Column(String(100), nullable=True)

    meta_data = Column(JSON, nullable=True)

    recommendation = relationship("Recommendation", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Feedback(id={self.id}, action_taken={self.action_taken}, rating={self.rating})>"
