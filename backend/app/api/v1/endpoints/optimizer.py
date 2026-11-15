import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.optimizer import TailoredResume
from app.modules.optimizer.service import optimizer_service
from app.schemas.optimizer import (
    ATSAnalysisResponse,
    CustomEvidenceRequest,
    ResumeCompositionIRResponse,
    SectionToggleRequest,
    TailoredBulletDiffResponse,
    TailoredResumeResponse,
    TailoredResumeSummaryResponse,
    TailorResumeRequest,
    UpdateDiffRequest,
)

router = APIRouter()


def _to_tailored_response(obj: TailoredResume) -> TailoredResumeResponse:
    diff_responses = [
        TailoredBulletDiffResponse(
            id=d.id,
            tailored_resume_id=d.tailored_resume_id,
            section_id=d.section_id,
            item_id=d.item_id,
            bullet_index=d.bullet_index,
            original_text=d.original_text,
            optimized_text=d.optimized_text,
            rationale=d.rationale,
            targeted_requirement_id=d.targeted_requirement_id,
            nli_verification_status=d.nli_verification_status,
            status=d.status,
            edited_text=d.edited_text,
            created_at=d.created_at,
        )
        for d in obj.diffs
    ]

    return TailoredResumeResponse(
        id=obj.id,
        user_id=obj.user_id,
        source_resume_id=obj.source_resume_id,
        target_jd_id=obj.target_jd_id,
        version_title=obj.version_title,
        job_title=obj.target_jd.job_title if obj.target_jd else "Target Role",
        company_name=obj.target_jd.company_name if obj.target_jd else None,
        tailored_content=obj.tailored_content,
        diffs_count=len(diff_responses),
        diffs=diff_responses,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.post(
    "/tailor",
    response_model=TailoredResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tailor resume bullets for target JD with NLI factual guardrails",
)
async def tailor_resume(
    payload: TailorResumeRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TailoredResumeResponse:
    """Generate role-targeted resume bullet rewrites enforcing strict NLI anti-hallucination verification
    and structured requirement-to-evidence mapping.
    """
    try:
        tailored = await optimizer_service.create_tailored_resume(
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

    return _to_tailored_response(tailored)


@router.get(
    "/tailored-resumes",
    response_model=list[TailoredResumeSummaryResponse],
    summary="List all tailored resume drafts for current user",
)
async def list_tailored_resumes(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[TailoredResumeSummaryResponse]:
    """Retrieve list of tailored resume versions."""
    resumes = await optimizer_service.list_user_tailored_resumes(db=db, user_id=user_id)
    return [
        TailoredResumeSummaryResponse(
            id=t.id,
            user_id=t.user_id,
            source_resume_id=t.source_resume_id,
            target_jd_id=t.target_jd_id,
            version_title=t.version_title,
            job_title=t.target_jd.job_title if t.target_jd else "Target Role",
            company_name=t.target_jd.company_name if t.target_jd else None,
            diffs_count=len(t.diffs),
            created_at=t.created_at,
        )
        for t in resumes
    ]


@router.get(
    "/tailored-resumes/{tailored_id}",
    response_model=TailoredResumeResponse,
    summary="Get tailored resume details, diffs, and live snapshot",
)
async def get_tailored_resume(
    tailored_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TailoredResumeResponse:
    """Retrieve full tailored resume snapshot and bullet diffs."""
    tailored = await optimizer_service.get_tailored_resume(
        db=db, user_id=user_id, tailored_id=tailored_id
    )
    if not tailored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tailored resume draft not found",
        )
    return _to_tailored_response(tailored)


@router.get(
    "/tailored-resumes/{tailored_id}/composition",
    response_model=ResumeCompositionIRResponse,
    summary="Get full structured intermediate representation (IR) of tailored resume",
)
async def get_composition_ir(
    tailored_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeCompositionIRResponse:
    """Retrieve full Composition Intermediate Representation (IR) with provenance and mappings."""
    try:
        ir = await optimizer_service.get_composition_ir(
            db=db, user_id=user_id, tailored_id=tailored_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    return ResumeCompositionIRResponse(**ir)


@router.put(
    "/tailored-resumes/{tailored_id}/sections",
    response_model=TailoredResumeResponse,
    summary="Toggle section inclusion or update display order",
)
async def update_section_visibility(
    tailored_id: uuid.UUID,
    payload: SectionToggleRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TailoredResumeResponse:
    """Toggle whether a section is included in the tailored resume or adjust display order."""
    try:
        tailored = await optimizer_service.update_section_visibility(
            db=db,
            user_id=user_id,
            tailored_id=tailored_id,
            section_id=payload.section_id,
            is_included=payload.is_included,
            display_order=payload.display_order,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    return _to_tailored_response(tailored)


@router.put(
    "/diffs/{diff_id}",
    response_model=TailoredBulletDiffResponse,
    summary="Accept, reject, or edit a tailored bullet diff",
)
async def update_diff(
    diff_id: uuid.UUID,
    payload: UpdateDiffRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TailoredBulletDiffResponse:
    """Accept, reject, or customize a bullet diff; dynamically updates the live resume snapshot."""
    try:
        diff = await optimizer_service.update_diff_status(
            db=db,
            user_id=user_id,
            diff_id=diff_id,
            new_status=payload.status,
            edited_text=payload.edited_text,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None

    return TailoredBulletDiffResponse(
        id=diff.id,
        tailored_resume_id=diff.tailored_resume_id,
        section_id=diff.section_id,
        item_id=diff.item_id,
        bullet_index=diff.bullet_index,
        original_text=diff.original_text,
        optimized_text=diff.optimized_text,
        rationale=diff.rationale,
        targeted_requirement_id=diff.targeted_requirement_id,
        nli_verification_status=diff.nli_verification_status,
        status=diff.status,
        edited_text=diff.edited_text,
        created_at=diff.created_at,
    )


@router.post(
    "/diffs/{diff_id}/restore",
    response_model=TailoredBulletDiffResponse,
    summary="Restore a tailored bullet diff to original source text",
)
async def restore_diff(
    diff_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TailoredBulletDiffResponse:
    """Explicitly restore a diff bullet back to the candidate's original text."""
    try:
        diff = await optimizer_service.restore_diff_to_original(
            db=db,
            user_id=user_id,
            diff_id=diff_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None

    return TailoredBulletDiffResponse(
        id=diff.id,
        tailored_resume_id=diff.tailored_resume_id,
        section_id=diff.section_id,
        item_id=diff.item_id,
        bullet_index=diff.bullet_index,
        original_text=diff.original_text,
        optimized_text=diff.optimized_text,
        rationale=diff.rationale,
        targeted_requirement_id=diff.targeted_requirement_id,
        nli_verification_status=diff.nli_verification_status,
        status=diff.status,
        edited_text=diff.edited_text,
        created_at=diff.created_at,
    )


@router.get(
    "/tailored-resumes/{tailored_id}/ats-analysis",
    response_model=ATSAnalysisResponse,
    summary="Get full ATS Job Compatibility and Readability Score analysis",
)
async def get_ats_analysis(
    tailored_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ATSAnalysisResponse:
    """Retrieve explainable dual-metric ATS analysis with byte-level extraction audit."""
    try:
        analysis = await optimizer_service.get_ats_analysis(
            db=db, user_id=user_id, tailored_id=tailored_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    return ATSAnalysisResponse(**analysis)


@router.post(
    "/tailored-resumes/{tailored_id}/custom-evidence",
    response_model=TailoredResumeResponse,
    summary="Attach verified candidate evidence to a requirement",
)
async def add_custom_evidence(
    tailored_id: uuid.UUID,
    payload: CustomEvidenceRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TailoredResumeResponse:
    """Attach candidate-verified evidence to a missing or transferable requirement."""
    try:
        tailored = await optimizer_service.add_custom_evidence(
            db=db,
            user_id=user_id,
            tailored_id=tailored_id,
            requirement_id=payload.requirement_id,
            evidence_text=payload.evidence_text,
            section_name=payload.section_name,
            match_category=payload.match_category,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    return _to_tailored_response(tailored)


@router.post(
    "/tailored-resumes/{tailored_id}/export-pdf",
    summary="Export ATS-compliant single-column PDF",
)
async def export_pdf(
    tailored_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Generate clean, single-column ATS-friendly PDF document."""
    try:
        pdf_bytes = await optimizer_service.export_pdf(
            db=db, user_id=user_id, tailored_id=tailored_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tailored_resume_{tailored_id}.pdf"'
        },
    )


@router.post(
    "/tailored-resumes/{tailored_id}/export-docx",
    summary="Export ATS-compliant DOCX document",
)
async def export_docx(
    tailored_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Generate clean, ATS-compliant Microsoft Word DOCX document."""
    try:
        docx_bytes = await optimizer_service.export_docx(
            db=db, user_id=user_id, tailored_id=tailored_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="tailored_resume_{tailored_id}.docx"'
        },
    )


@router.delete(
    "/tailored-resumes/{tailored_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tailored resume draft and its diffs",
)
async def delete_tailored_resume(
    tailored_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a tailored resume draft."""
    deleted = await optimizer_service.delete_tailored_resume(
        db=db, user_id=user_id, tailored_id=tailored_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tailored resume not found",
        )
