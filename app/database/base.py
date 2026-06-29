"""
Base model mixins for common database patterns.

Provides UUID primary keys, timestamps, and soft delete functionality.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr


class UUIDMixin:
    """Mixin for UUID primary key."""

    @declared_attr
    def id(cls) -> Mapped[str]:
        """UUID primary key column."""
        return mapped_column(
            CHAR(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            unique=True,
            nullable=False,
            index=True,
        )


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        """Created timestamp column."""
        from sqlalchemy.sql import func
        return mapped_column(
            DateTime,
            nullable=False,
            server_default=func.now(),
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        """Updated timestamp column."""
        from sqlalchemy.sql import func
        return mapped_column(
            DateTime,
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )


class BaseModel(UUIDMixin, TimestampMixin):
    """Base model with UUID primary key and timestamps."""

    __abstract__ = True
    __allow_unmapped__ = True  # Allow legacy annotations for SQLAlchemy 2.0+

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            dict: Model data as dictionary
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of model instance."""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"
