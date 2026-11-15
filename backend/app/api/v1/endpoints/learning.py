import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.modules.learning.service import learning_service
from app.schemas.learning import (
    GenerateRoadmapRequest,
    LearningMilestoneResponse,
    LearningRoadmapResponse,
    LearningRoadmapSummaryResponse,
    ReviewEvidenceRequest,
    SubmitEvidenceRequest,
    UpdateMilestoneRequest,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate personalized learning roadmap from skill gaps",
)
async def generate_roadmap(
    payload: GenerateRoadmapRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningRoadmapResponse:
    try:
        roadmap = await learning_service.create_roadmap(
            db=db,
            user_id=current_user_id,
            match_evaluation_id=payload.match_evaluation_id,
        )
        return LearningRoadmapResponse.model_validate(roadmap)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning roadmap: {e!s}",
        ) from e


@router.get(
    "",
    response_model=list[LearningRoadmapSummaryResponse],
    summary="List all learning roadmaps for current user",
)
async def list_roadmaps(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LearningRoadmapSummaryResponse]:
    roadmaps = await learning_service.list_roadmaps(db=db, user_id=current_user_id)
    return [LearningRoadmapSummaryResponse.model_validate(r) for r in roadmaps]


@router.get(
    "/{roadmap_id}",
    response_model=LearningRoadmapResponse,
    summary="Get learning roadmap with milestone details",
)
async def get_roadmap(
    roadmap_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningRoadmapResponse:
    roadmap = await learning_service.get_roadmap(
        db=db, user_id=current_user_id, roadmap_id=roadmap_id
    )
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning roadmap not found.",
        )
    return LearningRoadmapResponse.model_validate(roadmap)


@router.put(
    "/milestones/{milestone_id}",
    response_model=LearningMilestoneResponse,
    summary="Toggle milestone completion status",
)
async def toggle_milestone(
    milestone_id: uuid.UUID,
    payload: UpdateMilestoneRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningMilestoneResponse:
    try:
        milestone = await learning_service.toggle_milestone(
            db=db,
            user_id=current_user_id,
            milestone_id=milestone_id,
            is_completed=payload.is_completed,
        )
        return LearningMilestoneResponse.model_validate(milestone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update milestone: {e!s}",
        ) from e


@router.post(
    "/milestones/{milestone_id}/evidence",
    response_model=LearningMilestoneResponse,
    summary="Submit completed project evidence and verify milestone",
)
async def submit_milestone_evidence(
    milestone_id: uuid.UUID,
    payload: SubmitEvidenceRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningMilestoneResponse:
    try:
        milestone = await learning_service.submit_milestone_evidence(
            db=db,
            user_id=current_user_id,
            milestone_id=milestone_id,
            evidence=payload.model_dump(),
        )
        return LearningMilestoneResponse.model_validate(milestone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit evidence: {e!s}",
        ) from e


@router.post(
    "/milestones/{milestone_id}/review",
    response_model=LearningMilestoneResponse,
    summary="Review submitted deliverable evidence (VERIFIED or REJECTED)",
)
async def review_milestone_evidence(
    milestone_id: uuid.UUID,
    payload: ReviewEvidenceRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningMilestoneResponse:
    try:
        milestone = await learning_service.review_milestone_evidence(
            db=db,
            user_id=current_user_id,
            milestone_id=milestone_id,
            status=payload.status,
            reviewer_notes=payload.reviewer_notes,
        )
        return LearningMilestoneResponse.model_validate(milestone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review milestone: {e!s}",
        ) from e


@router.delete(
    "/{roadmap_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a learning roadmap",
)
async def delete_roadmap(
    roadmap_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await learning_service.delete_roadmap(
        db=db, user_id=current_user_id, roadmap_id=roadmap_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning roadmap not found.",
        )
