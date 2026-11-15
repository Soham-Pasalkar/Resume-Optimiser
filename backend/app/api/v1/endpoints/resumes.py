import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.modules.ingestion.service import IngestionService
from app.schemas.resume import (
    ResumeListItem,
    ResumeResponse,
    ResumeUploadResponse,
    SectionListUpdatePayload,
)

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a resume document (PDF or DOCX)",
)
async def upload_resume(
    file: Annotated[UploadFile, File(...)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    is_master: Annotated[bool, Form()] = False,
) -> ResumeUploadResponse:
    """Ingest a PDF or DOCX resume, extract text, detect sections, and persist."""
    service = IngestionService(db)
    resume = await service.process_resume_upload(user_id, file, is_master=is_master)

    return ResumeUploadResponse(
        resume_id=resume.id,
        file_name=resume.file_name,
        file_format=resume.file_format,
        status=resume.parsing_status,
        is_master=resume.is_master,
        ocr_applied=resume.ocr_applied,
        sections_detected=len(resume.sections),
        message="Resume successfully uploaded and parsed.",
    )


@router.get(
    "",
    response_model=list[ResumeListItem],
    summary="List all uploaded resumes for authenticated user",
)
async def list_resumes(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ResumeListItem]:
    """Retrieve summary list of all resumes belonging to current user."""
    service = IngestionService(db)
    resumes = await service.get_user_resumes(user_id)

    return [
        ResumeListItem(
            id=r.id,
            file_name=r.file_name,
            file_format=r.file_format,
            file_size_bytes=r.file_size_bytes,
            is_master=r.is_master,
            parsing_status=r.parsing_status,
            ocr_applied=r.ocr_applied,
            sections_count=len(r.sections),
            created_at=r.created_at,
        )
        for r in resumes
    ]


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get detailed resume with parsed sections and items",
)
async def get_resume_detail(
    resume_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeResponse:
    """Retrieve full resume structure with all detected sections and items."""
    service = IngestionService(db)
    resume = await service.get_resume_by_id(user_id, resume_id)
    return ResumeResponse.model_validate(resume)


@router.put(
    "/{resume_id}/sections",
    response_model=ResumeResponse,
    summary="Update parsed section text and headings manually",
)
async def update_resume_sections(
    resume_id: uuid.UUID,
    payload: SectionListUpdatePayload,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeResponse:
    """Allow user to edit or correct parsed section content before downstream processing."""
    service = IngestionService(db)
    updated = await service.update_sections(
        user_id,
        resume_id,
        [s.model_dump(exclude_unset=True) for s in payload.sections],
    )
    return ResumeResponse.model_validate(updated)


@router.put(
    "/{resume_id}/set-master",
    response_model=ResumeResponse,
    summary="Set designated resume as active master profile source",
)
async def set_master_resume(
    resume_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeResponse:
    """Designate resume as active master profile source."""
    service = IngestionService(db)
    updated = await service.set_master_resume(user_id, resume_id)
    return ResumeResponse.model_validate(updated)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete resume and remove stored file",
)
async def delete_resume(
    resume_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Permanently delete resume record and clean up stored file."""
    service = IngestionService(db)
    await service.delete_resume(user_id, resume_id)
    return {
        "status": "deleted",
        "resume_id": str(resume_id),
        "message": "Resume successfully deleted.",
    }
