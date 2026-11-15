import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class GenerateRoadmapRequest(BaseModel):
    match_evaluation_id: uuid.UUID


class CuratedResource(BaseModel):
    title: str
    url: str
    type: str = "Documentation"


class LearningMilestoneResponse(BaseModel):
    id: uuid.UUID
    roadmap_id: uuid.UUID
    sequence_order: int
    skill_name: str
    milestone_title: str
    description: str
    curated_resources: list[dict[str, Any]] = Field(default_factory=list)
    practical_project_brief: str | None = None
    why_it_matters: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    practical_exercises: list[str] = Field(default_factory=list)
    expected_deliverables: list[str] = Field(default_factory=list)
    verification_criteria: list[str] = Field(default_factory=list)
    estimated_hours: int = 10
    completed_evidence: dict[str, Any] | None = None
    evidence_verified: bool = False
    verification_status: str = "UNSUBMITTED"
    is_completed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateMilestoneRequest(BaseModel):
    is_completed: bool


class SubmitEvidenceRequest(BaseModel):
    evidence_text: str = Field(..., min_length=5, description="Factual description of completed deliverable or project findings")
    github_url: str | None = None
    demo_url: str | None = None
    test_results: str | None = None

    @field_validator("github_url", "demo_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if not v:
            return None
        import urllib.parse
        parsed = urllib.parse.urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid URL '{v}'. Must be a valid HTTP or HTTPS URL.")
        return v.strip()


class ReviewEvidenceRequest(BaseModel):
    status: str = Field(..., description="VERIFIED or REJECTED")
    reviewer_notes: str | None = None


class LearningRoadmapResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_evaluation_id: uuid.UUID
    target_role_title: str
    estimated_total_hours: int | None = 40
    status: str
    milestones: list[LearningMilestoneResponse] = Field(default_factory=list)
    completed_count: int = 0
    total_milestones: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class LearningRoadmapSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_evaluation_id: uuid.UUID
    target_role_title: str
    estimated_total_hours: int | None = 40
    status: str
    milestones_count: int = 0
    completed_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
