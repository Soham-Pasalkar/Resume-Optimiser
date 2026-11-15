import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.modules.candidate.service import candidate_service
from app.schemas.candidate import (
    AddCustomSkillRequest,
    BuildProfileRequest,
    CandidateSkillResponse,
    VerifySkillRequest,
)

router = APIRouter()


@router.post(
    "/build-profile",
    response_model=list[CandidateSkillResponse],
    summary="Build or update master candidate profile competencies from resume",
)
async def build_candidate_profile(
    payload: BuildProfileRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CandidateSkillResponse]:
    """Extract factual competencies from candidate resume anchored to verbatim evidence."""
    skills = await candidate_service.build_or_update_profile(
        db=db,
        user_id=user_id,
        resume_id=payload.resume_id,
    )
    return skills


@router.get(
    "/profile",
    response_model=list[CandidateSkillResponse],
    summary="Get candidate profile competencies and evidence",
)
async def get_candidate_profile(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CandidateSkillResponse]:
    """Retrieve all extracted candidate skills with supporting evidence."""
    skills = await candidate_service.get_profile(db=db, user_id=user_id)
    return skills


@router.post(
    "/verify-skill",
    response_model=CandidateSkillResponse,
    summary="Toggle user verification status on a candidate skill",
)
async def verify_candidate_skill(
    payload: VerifySkillRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateSkillResponse:
    """Explicitly verify or unverify that the candidate possesses this skill."""
    skill = await candidate_service.verify_skill(
        db=db,
        user_id=user_id,
        skill_id=payload.skill_id,
        is_verified=payload.is_verified,
    )
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate skill not found",
        )
    return skill


@router.post(
    "/skills",
    response_model=CandidateSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a custom skill to candidate profile",
)
async def add_custom_skill(
    payload: AddCustomSkillRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateSkillResponse:
    """Manually add or update a verified skill on candidate profile."""
    skill = await candidate_service.add_custom_skill(
        db=db,
        user_id=user_id,
        skill_name=payload.skill_name,
        category=payload.category,
        proficiency_level=payload.proficiency_level,
        evidence_text=payload.evidence_text,
    )
    return skill


@router.delete(
    "/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a skill from candidate profile",
)
async def delete_candidate_skill(
    skill_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove a candidate skill by ID."""
    deleted = await candidate_service.delete_skill(
        db=db,
        user_id=user_id,
        skill_id=skill_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate skill not found",
        )
