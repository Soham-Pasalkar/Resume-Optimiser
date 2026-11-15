import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JDAnalyzeRequest(BaseModel):
    raw_text: str = Field(..., min_length=20, description="Full job description text")
    job_title: str | None = Field(
        default=None, max_length=255, description="Optional custom job title override"
    )
    company_name: str | None = Field(
        default=None, max_length=255, description="Optional hiring company name"
    )


class JDRequirementResponse(BaseModel):
    id: uuid.UUID
    jd_id: uuid.UUID
    requirement_text: str
    category: str
    is_mandatory: bool
    importance_weight: float
    min_years_experience: float | None = None
    canonical_skill_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_title: str
    company_name: str | None = None
    department: str | None = None
    seniority_level: str | None = None
    work_mode: str | None = None
    location: str | None = None
    salary_range: str | None = None
    raw_text: str
    requirements: list[JDRequirementResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class JobDescriptionSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_title: str
    company_name: str | None = None
    seniority_level: str | None = None
    work_mode: str | None = None
    location: str | None = None
    requirements_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
