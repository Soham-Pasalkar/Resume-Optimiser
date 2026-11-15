import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.modules.jd_engine.service import jd_service
from app.schemas.jd import (
    JDAnalyzeRequest,
    JobDescriptionResponse,
    JobDescriptionSummaryResponse,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze and decompose a raw job description",
)
async def analyze_job_description(
    payload: JDAnalyzeRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobDescriptionResponse:
    """Analyze job description text using local LLM with rule-based fallback.
    Extracts seniority, work mode, salary, and decomposes requirements into
    mandatory vs preferred taxonomy with canonical skill ontology links.
    """
    jd = await jd_service.analyze_and_store(
        db=db,
        user_id=user_id,
        raw_text=payload.raw_text,
        custom_title=payload.job_title,
        company_name=payload.company_name,
    )
    return jd


@router.get(
    "",
    response_model=list[JobDescriptionSummaryResponse],
    summary="List all job descriptions for current user",
)
async def list_job_descriptions(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[JobDescriptionSummaryResponse]:
    """Retrieve list of analyzed job descriptions for the authenticated user."""
    jds = await jd_service.get_user_jds(db=db, user_id=user_id)
    return [
        JobDescriptionSummaryResponse(
            id=jd.id,
            user_id=jd.user_id,
            job_title=jd.job_title,
            company_name=jd.company_name,
            seniority_level=jd.seniority_level,
            work_mode=jd.work_mode,
            location=jd.location,
            requirements_count=len(jd.requirements),
            created_at=jd.created_at,
        )
        for jd in jds
    ]


@router.get(
    "/{jd_id}",
    response_model=JobDescriptionResponse,
    summary="Get detailed job description with decomposed requirements",
)
async def get_job_description(
    jd_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobDescriptionResponse:
    """Retrieve complete decomposed job description by ID."""
    jd = await jd_service.get_jd_by_id(db=db, user_id=user_id, jd_id=jd_id)
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )
    return jd


@router.delete(
    "/{jd_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job description and its requirements",
)
async def delete_job_description(
    jd_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a job description by ID."""
    deleted = await jd_service.delete_jd(db=db, user_id=user_id, jd_id=jd_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found",
        )
