import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TailorResumeRequest(BaseModel):
    resume_id: uuid.UUID
    jd_id: uuid.UUID


class TailoredBulletDiffResponse(BaseModel):
    id: uuid.UUID
    tailored_resume_id: uuid.UUID
    section_id: str | None = None
    item_id: str | None = None
    bullet_index: int = 0
    original_text: str
    optimized_text: str
    rationale: str
    targeted_requirement_id: uuid.UUID | None = None
    nli_verification_status: str
    status: str
    edited_text: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateDiffRequest(BaseModel):
    status: str = Field(..., description="ACCEPTED, REJECTED, EDITED, or RESTORED")
    edited_text: str | None = Field(
        default=None, description="Customized bullet text if status is EDITED"
    )


class RequirementEvidenceMappingResponse(BaseModel):
    requirement_id: str
    requirement_text: str
    is_mandatory: bool
    canonical_skill_name: str | None = None
    category: str | None = None
    matched_section_id: str | None = None
    matched_section_name: str | None = None
    matched_item_id: str | None = None
    matched_bullet_index: int | None = None
    original_evidence_text: str | None = None
    matching_method: str = "UNMATCHED"
    confidence_score: float = 0.0
    verification_status: str = "UNMATCHED"


class MissingRequirementResponse(BaseModel):
    requirement_id: str
    requirement_text: str
    is_mandatory: bool
    canonical_skill_name: str | None = None
    category: str | None = None
    suggested_action: str


class ContentDecisionResponse(BaseModel):
    section_id: str
    section_type: str
    heading: str
    item_id: str | None = None
    bullet_index: int | None = None
    content_text: str
    decision: str
    relevance_score: float = 0.0
    matched_requirement_ids: list[str] = Field(default_factory=list)
    reasoning: str


class SectionToggleRequest(BaseModel):
    section_id: str
    is_included: bool
    display_order: int | None = None


class ResumeCompositionIRResponse(BaseModel):
    candidate_identity: dict[str, Any]
    sections: list[dict[str, Any]]
    export_sections: list[dict[str, Any]]
    provenance: list[dict[str, Any]]
    metadata: dict[str, Any]
    requirement_mappings: list[RequirementEvidenceMappingResponse] = Field(default_factory=list)
    missing_requirements: list[MissingRequirementResponse] = Field(default_factory=list)


class TailoredResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_resume_id: uuid.UUID
    target_jd_id: uuid.UUID
    version_title: str
    job_title: str | None = None
    company_name: str | None = None
    tailored_content: dict[str, Any] = Field(default_factory=dict)
    diffs_count: int = 0
    diffs: list[TailoredBulletDiffResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TailoredResumeSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_resume_id: uuid.UUID
    target_jd_id: uuid.UUID
    version_title: str
    job_title: str | None = None
    company_name: str | None = None
    diffs_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
