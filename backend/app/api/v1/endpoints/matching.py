import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.matching import MatchEvaluation
from app.modules.matching.scorer import hybrid_matching_engine
from app.modules.matching.service import matching_service
from app.schemas.matching import (
    MatchEvaluateRequest,
    MatchEvaluationResponse,
    MatchSummaryResponse,
    SkillGapItemResponse,
    SubScores,
    VerifyGapRequest,
)

router = APIRouter()


def _to_match_response(eval_obj: MatchEvaluation) -> MatchEvaluationResponse:
    gap_items = []
    for g in eval_obj.gap_items:
        req = g.requirement
        gap_items.append(
            SkillGapItemResponse(
                id=g.id,
                match_evaluation_id=g.match_evaluation_id,
                requirement_id=g.requirement_id,
                requirement_text=req.requirement_text if req else None,
                category=req.category if req else None,
                is_mandatory=req.is_mandatory if req else None,
                status=g.status,
                gap_severity=g.gap_severity,
                evidence_snippet=g.evidence_snippet,
                similarity_score=g.similarity_score,
                suggested_action=g.suggested_action,
                is_resolved=g.is_resolved,
                created_at=g.created_at,
            )
        )

    return MatchEvaluationResponse(
        id=eval_obj.id,
        user_id=eval_obj.user_id,
        resume_id=eval_obj.resume_id,
        jd_id=eval_obj.jd_id,
        job_title=eval_obj.job_description.job_title if eval_obj.job_description else "Position",
        company_name=eval_obj.job_description.company_name if eval_obj.job_description else None,
        overall_score=eval_obj.overall_score,
        rating_label=hybrid_matching_engine._get_rating_label(eval_obj.overall_score),
        sub_scores=SubScores(
            skill_match=eval_obj.skill_match_score,
            semantic_similarity=eval_obj.semantic_score,
            lexical_bm25=eval_obj.lexical_score,
            experience_depth=eval_obj.experience_score,
            domain_relevance=eval_obj.domain_score,
        ),
        scoring_breakdown=eval_obj.scoring_breakdown,
        summary_analysis=eval_obj.summary_analysis,
        gap_items=gap_items,
        created_at=eval_obj.created_at,
    )


@router.post(
    "/evaluate",
    response_model=MatchEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger hybrid candidate-role matching evaluation",
)
async def evaluate_match(
    payload: MatchEvaluateRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchEvaluationResponse:
    """Run multi-factor hybrid matching between a candidate resume and job description.
    Integrates BM25 lexical search, dense semantic similarity, and skill ontology overlap.
    """
    try:
        eval_obj = await matching_service.evaluate_match(
            db=db,
            user_id=user_id,
            resume_id=payload.resume_id,
            jd_id=payload.jd_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None

    return _to_match_response(eval_obj)


@router.get(
    "",
    response_model=list[MatchSummaryResponse],
    summary="List all match evaluations for authenticated user",
)
async def list_matches(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MatchSummaryResponse]:
    """Retrieve historical match evaluations for current user."""
    matches = await matching_service.list_user_matches(db=db, user_id=user_id)
    return [
        MatchSummaryResponse(
            id=m.id,
            user_id=m.user_id,
            resume_id=m.resume_id,
            jd_id=m.jd_id,
            job_title=m.job_description.job_title if m.job_description else "Position",
            company_name=m.job_description.company_name if m.job_description else None,
            overall_score=m.overall_score,
            rating_label=hybrid_matching_engine._get_rating_label(m.overall_score),
            created_at=m.created_at,
        )
        for m in matches
    ]


@router.get(
    "/{match_id}",
    response_model=MatchEvaluationResponse,
    summary="Get detailed match evaluation with 5-factor scoring and gaps",
)
async def get_match_detail(
    match_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchEvaluationResponse:
    """Retrieve complete explainable match report by ID."""
    eval_obj = await matching_service.get_match_by_id(db=db, user_id=user_id, match_id=match_id)
    if not eval_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match evaluation not found",
        )
    return _to_match_response(eval_obj)


@router.get(
    "/{match_id}/gaps",
    response_model=list[SkillGapItemResponse],
    summary="Get skill gap items for a match evaluation",
)
async def get_match_gaps(
    match_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SkillGapItemResponse]:
    """Retrieve 4-tier requirement gap items for an evaluation."""
    eval_obj = await matching_service.get_match_by_id(db=db, user_id=user_id, match_id=match_id)
    if not eval_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match evaluation not found",
        )
    resp = _to_match_response(eval_obj)
    return resp.gap_items


@router.post(
    "/{match_id}/gaps/verify",
    response_model=MatchEvaluationResponse,
    summary="Verify an unevidenced capability and recalculate score",
)
async def verify_match_gap(
    match_id: uuid.UUID,
    payload: VerifyGapRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchEvaluationResponse:
    """Verify candidate experience on a gap item and dynamically boost match score."""
    eval_obj = await matching_service.verify_gap(
        db=db,
        user_id=user_id,
        match_id=match_id,
        gap_item_id=payload.gap_item_id,
        has_experience=payload.has_experience,
        years_experience=payload.years_experience,
        verification_evidence=payload.verification_evidence,
    )
    if not eval_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match evaluation or gap item not found",
        )
    return _to_match_response(eval_obj)


@router.delete(
    "/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a match evaluation and its gap items",
)
async def delete_match(
    match_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a match evaluation."""
    deleted = await matching_service.delete_match(db=db, user_id=user_id, match_id=match_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match evaluation not found",
        )
