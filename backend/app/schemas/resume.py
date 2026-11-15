import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResumeItemResponse(BaseModel):
    id: uuid.UUID
    section_id: uuid.UUID
    item_type: str
    title: str
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    bullets: list[Any] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeSectionUpdate(BaseModel):
    id: uuid.UUID
    heading: str | None = None
    raw_content: str | None = None
    section_type: str | None = None
    display_order: int | None = None


class ResumeSectionResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    section_type: str
    heading: str
    raw_content: str
    display_order: int
    items: list[ResumeItemResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    file_key: str
    file_format: str
    file_size_bytes: int
    raw_text: str
    is_master: bool
    parsing_status: str
    ocr_applied: bool
    created_at: datetime
    updated_at: datetime
    sections: list[ResumeSectionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ResumeListItem(BaseModel):
    id: uuid.UUID
    file_name: str
    file_format: str
    file_size_bytes: int
    is_master: bool
    parsing_status: str
    ocr_applied: bool
    sections_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    resume_id: uuid.UUID
    file_name: str
    file_format: str
    status: str
    is_master: bool
    ocr_applied: bool
    sections_detected: int
    message: str


class SectionListUpdatePayload(BaseModel):
    sections: list[ResumeSectionUpdate]
