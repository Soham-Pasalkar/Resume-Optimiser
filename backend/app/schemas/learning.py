import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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
    is_completed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateMilestoneRequest(BaseModel):
    is_completed: bool


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
