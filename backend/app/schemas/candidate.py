import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CandidateSkillResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    skill_name: str
    normalized_name: str
    category: str
    proficiency_level: str | None = "proficient"
    years_experience: float | None = None
    evidence_text: str | None = None
    evidence_item_id: str | None = None
    is_user_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class BuildProfileRequest(BaseModel):
    resume_id: uuid.UUID | None = Field(
        default=None, description="Optional specific resume to build profile from"
    )


class VerifySkillRequest(BaseModel):
    skill_id: uuid.UUID
    is_verified: bool = True


class AddCustomSkillRequest(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    proficiency_level: str = Field(default="proficient", max_length=50)
    evidence_text: str | None = None
