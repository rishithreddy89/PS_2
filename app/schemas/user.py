"""
User Pydantic schemas for API validation.
"""

from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.base import BaseResponse, BaseSchema


class UserBase(BaseSchema):
    """Base user schema."""

    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role: str = Field(..., description="User role")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=100, description="User password")


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: Optional[EmailStr] = Field(None, description="User email address")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name")
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Active status")


class UserResponse(UserBase, BaseResponse):
    """Schema for user response."""

    is_active: bool = Field(..., description="Active status")
    is_superuser: bool = Field(..., description="Superuser status")


class UserLogin(BaseSchema):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseSchema):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
