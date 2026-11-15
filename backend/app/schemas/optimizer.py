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
    status: str = Field(..., description="ACCEPTED, REJECTED, or EDITED")
    edited_text: str | None = Field(
        default=None, description="Customized bullet text if status is EDITED"
    )


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
