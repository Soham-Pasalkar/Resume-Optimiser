import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MatchEvaluateRequest(BaseModel):
    resume_id: uuid.UUID
    jd_id: uuid.UUID


class SkillGapItemResponse(BaseModel):
    id: uuid.UUID
    match_evaluation_id: uuid.UUID
    requirement_id: uuid.UUID
    requirement_text: str | None = None
    category: str | None = None
    is_mandatory: bool | None = None
    status: str
    gap_severity: str
    evidence_snippet: str | None = None
    similarity_score: float | None = None
    suggested_action: str | None = None
    is_resolved: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SubScores(BaseModel):
    skill_match: float
    semantic_similarity: float
    lexical_bm25: float
    experience_depth: float
    domain_relevance: float


class MatchEvaluationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    jd_id: uuid.UUID
    job_title: str | None = None
    company_name: str | None = None
    overall_score: float
    rating_label: str
    sub_scores: SubScores
    scoring_breakdown: dict[str, Any] = Field(default_factory=dict)
    summary_analysis: str | None = None
    gap_items: list[SkillGapItemResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class MatchSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    jd_id: uuid.UUID
    job_title: str
    company_name: str | None = None
    overall_score: float
    rating_label: str
    created_at: datetime

    class Config:
        from_attributes = True


class VerifyGapRequest(BaseModel):
    gap_item_id: uuid.UUID
    has_experience: bool = True
    years_experience: float | None = None
    verification_evidence: str | None = None
