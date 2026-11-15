import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.modules.interview.service import interview_service
from app.schemas.interview import (
    EvaluateAnswerRequest,
    GenerateInterviewPrepRequest,
    InterviewPrepResponse,
    InterviewPrepSummaryResponse,
    InterviewQuestionResponse,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=InterviewPrepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate tailored technical, behavioral STAR, and gap-defense interview questions",
)
async def generate_interview_prep(
    payload: GenerateInterviewPrepRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewPrepResponse:
    try:
        prep = await interview_service.create_interview_prep(
            db=db,
            user_id=current_user_id,
            match_evaluation_id=payload.match_evaluation_id,
        )
        return InterviewPrepResponse.model_validate(prep)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interview prep: {e!s}",
        ) from e


@router.get(
    "",
    response_model=list[InterviewPrepSummaryResponse],
    summary="List all interview preparation sessions for current user",
)
async def list_interview_preps(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InterviewPrepSummaryResponse]:
    preps = await interview_service.list_interview_preps(db=db, user_id=current_user_id)
    return [InterviewPrepSummaryResponse.model_validate(p) for p in preps]


@router.get(
    "/{prep_id}",
    response_model=InterviewPrepResponse,
    summary="Get interview prep session with all questions and evaluation feedback",
)
async def get_interview_prep(
    prep_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewPrepResponse:
    prep = await interview_service.get_interview_prep(
        db=db, user_id=current_user_id, prep_id=prep_id
    )
    if not prep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview preparation session not found.",
        )
    return InterviewPrepResponse.model_validate(prep)


@router.post(
    "/questions/{question_id}/evaluate",
    response_model=InterviewQuestionResponse,
    summary="Submit candidate response and evaluate against rubric using AI",
)
async def evaluate_answer(
    question_id: uuid.UUID,
    payload: EvaluateAnswerRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewQuestionResponse:
    try:
        question = await interview_service.evaluate_answer(
            db=db,
            user_id=current_user_id,
            question_id=question_id,
            candidate_response=payload.practice_response,
        )
        return InterviewQuestionResponse.model_validate(question)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate answer: {e!s}",
        ) from e


@router.delete(
    "/{prep_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an interview preparation session",
)
async def delete_interview_prep(
    prep_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await interview_service.delete_interview_prep(
        db=db, user_id=current_user_id, prep_id=prep_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview preparation session not found.",
        )
