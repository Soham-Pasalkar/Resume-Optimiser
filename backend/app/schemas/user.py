import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserProfileBase(BaseModel):
    headline: str | None = None
    target_role_title: str | None = None
    target_seniority: str | None = None
    years_of_experience: float | None = Field(None, ge=0, le=50)
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)


class UserRegister(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    profile: UserProfileUpdate | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: UserProfileResponse | None = None

    class Config:
        from_attributes = True
