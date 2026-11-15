import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationActivityResponse(BaseModel):
    id: uuid.UUID
    activity_type: str
    from_stage: str | None = None
    to_stage: str | None = None
    note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobApplicationCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    job_title: str = Field(..., min_length=1, max_length=255)
    job_description_id: uuid.UUID | None = None
    tailored_resume_id: uuid.UUID | None = None
    match_evaluation_id: uuid.UUID | None = None
    location: str | None = None
    stage: str = Field(default="WISHLIST")
    priority: str = Field(default="MEDIUM")
    salary_range: str | None = None
    job_url: str | None = None
    applied_date: datetime | None = None
    deadline: datetime | None = None
    notes: str | None = None


class JobApplicationUpdate(BaseModel):
    company_name: str | None = None
    job_title: str | None = None
    job_description_id: uuid.UUID | None = None
    tailored_resume_id: uuid.UUID | None = None
    match_evaluation_id: uuid.UUID | None = None
    location: str | None = None
    stage: str | None = None
    priority: str | None = None
    salary_range: str | None = None
    job_url: str | None = None
    applied_date: datetime | None = None
    deadline: datetime | None = None
    notes: str | None = None
    is_archived: bool | None = None


class ApplicationStageUpdate(BaseModel):
    stage: str = Field(..., description="Target stage for application")
    note: str | None = Field(None, description="Optional log note for the stage transition")


class JobApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_description_id: uuid.UUID | None = None
    tailored_resume_id: uuid.UUID | None = None
    match_evaluation_id: uuid.UUID | None = None
    company_name: str
    job_title: str
    location: str | None = None
    stage: str
    priority: str
    salary_range: str | None = None
    job_url: str | None = None
    applied_date: datetime | None = None
    deadline: datetime | None = None
    notes: str | None = None
    is_archived: bool
    match_score: float | None = None
    tailored_resume_title: str | None = None
    activities: list[ApplicationActivityResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobApplicationSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    job_title: str
    location: str | None = None
    stage: str
    priority: str
    salary_range: str | None = None
    match_score: float | None = None
    applied_date: datetime | None = None
    is_archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OpportunityComparisonRequest(BaseModel):
    application_ids: list[uuid.UUID] = Field(..., min_length=2, max_length=5)


class OpportunityComparisonItem(BaseModel):
    application_id: uuid.UUID
    company_name: str
    job_title: str
    location: str | None = None
    stage: str
    priority: str
    salary_range: str | None = None
    overall_match_score: float | None = None
    skill_match_score: float | None = None
    experience_score: float | None = None
    top_demonstrated_skills: list[str] = Field(default_factory=list)
    critical_missing_skills: list[str] = Field(default_factory=list)


class OpportunityComparisonResponse(BaseModel):
    opportunities: list[OpportunityComparisonItem]
    comparison_summary: str
