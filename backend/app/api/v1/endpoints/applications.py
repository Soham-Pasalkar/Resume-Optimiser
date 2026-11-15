import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.application import JobApplication
from app.modules.application.service import application_service
from app.schemas.application import (
    ApplicationActivityResponse,
    ApplicationStageUpdate,
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationSummaryResponse,
    JobApplicationUpdate,
    OpportunityComparisonRequest,
    OpportunityComparisonResponse,
)

router = APIRouter()


def _to_application_response(obj: JobApplication) -> JobApplicationResponse:
    match_score = obj.match_evaluation.overall_score if obj.match_evaluation else None
    resume_title = obj.tailored_resume.version_title if obj.tailored_resume else None
    return JobApplicationResponse(
        id=obj.id,
        user_id=obj.user_id,
        job_description_id=obj.job_description_id,
        tailored_resume_id=obj.tailored_resume_id,
        match_evaluation_id=obj.match_evaluation_id,
        company_name=obj.company_name,
        job_title=obj.job_title,
        location=obj.location,
        stage=obj.stage,
        priority=obj.priority,
        salary_range=obj.salary_range,
        job_url=obj.job_url,
        applied_date=obj.applied_date,
        deadline=obj.deadline,
        notes=obj.notes,
        is_archived=obj.is_archived,
        match_score=match_score,
        tailored_resume_title=resume_title,
        activities=[ApplicationActivityResponse.model_validate(act) for act in obj.activities],
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


def _to_summary_response(obj: JobApplication) -> JobApplicationSummaryResponse:
    match_score = obj.match_evaluation.overall_score if obj.match_evaluation else None
    return JobApplicationSummaryResponse(
        id=obj.id,
        user_id=obj.user_id,
        company_name=obj.company_name,
        job_title=obj.job_title,
        location=obj.location,
        stage=obj.stage,
        priority=obj.priority,
        salary_range=obj.salary_range,
        match_score=match_score,
        applied_date=obj.applied_date,
        is_archived=obj.is_archived,
        created_at=obj.created_at,
    )


@router.post(
    "",
    response_model=JobApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job application tracking record",
)
async def create_application(
    payload: JobApplicationCreate,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobApplicationResponse:
    try:
        app = await application_service.create_application(
            db=db,
            user_id=current_user_id,
            payload=payload,
        )
        return _to_application_response(app)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job application: {e!s}",
        ) from e


@router.get(
    "",
    response_model=list[JobApplicationSummaryResponse],
    summary="List job applications for current user with stage and search filters",
)
async def list_applications(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    stage: str | None = Query(
        None,
        description="Filter by stage: WISHLIST, APPLIED, SCREENING, INTERVIEWING, OFFER, REJECTED",
    ),
    include_archived: bool = Query(False, description="Include archived applications"),
    search: str | None = Query(None, description="Search company or title"),
) -> list[JobApplicationSummaryResponse]:
    apps = await application_service.list_applications(
        db=db,
        user_id=current_user_id,
        stage=stage,
        include_archived=include_archived,
        search=search,
    )
    return [_to_summary_response(a) for a in apps]


@router.post(
    "/compare",
    response_model=OpportunityComparisonResponse,
    summary="Compare 2 to 5 opportunities side-by-side using qualification metrics",
)
async def compare_opportunities(
    payload: OpportunityComparisonRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OpportunityComparisonResponse:
    try:
        return await application_service.compare_opportunities(
            db=db,
            user_id=current_user_id,
            application_ids=payload.application_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare opportunities: {e!s}",
        ) from e


@router.get(
    "/{application_id}",
    response_model=JobApplicationResponse,
    summary="Get job application detail with activity timeline and linked assets",
)
async def get_application(
    application_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobApplicationResponse:
    app = await application_service.get_application(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    )
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )
    return _to_application_response(app)


@router.put(
    "/{application_id}",
    response_model=JobApplicationResponse,
    summary="Update job application details",
)
async def update_application(
    application_id: uuid.UUID,
    payload: JobApplicationUpdate,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobApplicationResponse:
    try:
        app = await application_service.update_application(
            db=db,
            user_id=current_user_id,
            application_id=application_id,
            payload=payload,
        )
        return _to_application_response(app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job application: {e!s}",
        ) from e


@router.patch(
    "/{application_id}/stage",
    response_model=JobApplicationResponse,
    summary="Quickly advance or update application stage (e.g. kanban drag-and-drop)",
)
async def update_stage(
    application_id: uuid.UUID,
    payload: ApplicationStageUpdate,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobApplicationResponse:
    try:
        app = await application_service.update_application_stage(
            db=db,
            user_id=current_user_id,
            application_id=application_id,
            new_stage=payload.stage,
            note=payload.note,
        )
        return _to_application_response(app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stage: {e!s}",
        ) from e


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job application record",
)
async def delete_application(
    application_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await application_service.delete_application(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )
