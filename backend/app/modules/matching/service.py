import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.jd import JobDescription
from app.models.matching import MatchEvaluation, SkillGapItem
from app.models.resume import Resume, ResumeSection
from app.modules.candidate.service import candidate_service
from app.modules.matching.scorer import hybrid_matching_engine


class MatchingService:
    """Orchestrates candidate-role matching evaluation, scoring persistence, and gap resolution."""

    async def evaluate_match(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        jd_id: uuid.UUID,
    ) -> MatchEvaluation:
        # 1. Fetch Resume with all nested sections and items
        resume_stmt = (
            select(Resume)
            .where(Resume.id == resume_id, Resume.user_id == user_id)
            .options(selectinload(Resume.sections).selectinload(ResumeSection.items))
        )
        resume_res = await db.execute(resume_stmt)
        resume = resume_res.scalar_one_or_none()
        if not resume:
            raise ValueError("Resume not found or does not belong to authenticated user.")

        # 2. Fetch Job Description with requirements
        jd_stmt = (
            select(JobDescription)
            .where(JobDescription.id == jd_id, JobDescription.user_id == user_id)
            .options(selectinload(JobDescription.requirements))
        )
        jd_res = await db.execute(jd_stmt)
        jd = jd_res.scalar_one_or_none()
        if not jd:
            raise ValueError("Job description not found or does not belong to authenticated user.")

        # 3. Fetch candidate profile skills
        candidate_skills = await candidate_service.get_profile(db, user_id)

        # 4. Run hybrid matching evaluation
        scoring = await hybrid_matching_engine.evaluate(
            resume=resume,
            jd=jd,
            candidate_skills=candidate_skills,
        )

        # 5. Persist MatchEvaluation
        match_eval = MatchEvaluation(
            user_id=user_id,
            resume_id=resume.id,
            jd_id=jd.id,
            overall_score=scoring.overall_score,
            lexical_score=scoring.lexical_score,
            semantic_score=scoring.semantic_score,
            skill_match_score=scoring.skill_match_score,
            experience_score=scoring.experience_score,
            domain_score=scoring.domain_score,
            scoring_breakdown=scoring.scoring_breakdown,
            summary_analysis=scoring.summary_analysis,
        )
        db.add(match_eval)
        await db.flush()

        # 6. Persist SkillGapItems
        for gap in scoring.gap_evaluations:
            gap_item = SkillGapItem(
                match_evaluation_id=match_eval.id,
                requirement_id=gap["requirement_id"],
                status=gap["status"],
                gap_severity=gap["gap_severity"],
                evidence_snippet=gap.get("evidence_snippet"),
                similarity_score=gap.get("similarity_score"),
                suggested_action=gap.get("suggested_action"),
                is_resolved=gap.get("is_resolved", False),
            )
            db.add(gap_item)

        await db.commit()

        # 7. Reload and return complete evaluation
        return await self.get_match_by_id(db, user_id, match_eval.id)  # type: ignore

    async def get_match_by_id(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        match_id: uuid.UUID,
    ) -> MatchEvaluation | None:
        stmt = (
            select(MatchEvaluation)
            .where(MatchEvaluation.id == match_id, MatchEvaluation.user_id == user_id)
            .options(
                selectinload(MatchEvaluation.gap_items),
                selectinload(MatchEvaluation.resume),
                selectinload(MatchEvaluation.job_description),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_matches(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[MatchEvaluation]:
        stmt = (
            select(MatchEvaluation)
            .where(MatchEvaluation.user_id == user_id)
            .order_by(MatchEvaluation.created_at.desc())
            .options(
                selectinload(MatchEvaluation.resume),
                selectinload(MatchEvaluation.job_description),
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def verify_gap(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        match_id: uuid.UUID,
        gap_item_id: uuid.UUID,
        has_experience: bool,
        years_experience: float | None = None,
        verification_evidence: str | None = None,
    ) -> MatchEvaluation | None:
        match_eval = await self.get_match_by_id(db, user_id, match_id)
        if not match_eval:
            return None

        # Find target gap item
        target_gap = next((g for g in match_eval.gap_items if g.id == gap_item_id), None)
        if not target_gap:
            return None

        if has_experience:
            target_gap.status = "DEMONSTRATED"
            target_gap.gap_severity = "LOW"
            target_gap.is_resolved = True
            if verification_evidence:
                target_gap.evidence_snippet = verification_evidence

            # Add / update to CandidateSkill master profile as verified
            req = target_gap.requirement
            skill_name = req.canonical_skill_name or req.requirement_text[:50]
            await candidate_service.add_custom_skill(
                db=db,
                user_id=user_id,
                skill_name=skill_name,
                category=req.category,
                proficiency_level="proficient",
                evidence_text=verification_evidence,
            )

            # Boost scores proportionally
            boost = 5.0 if req.is_mandatory else 2.5
            match_eval.overall_score = round(min(100.0, match_eval.overall_score + boost), 2)
            match_eval.skill_match_score = round(
                min(100.0, match_eval.skill_match_score + (boost * 1.5)), 2
            )

            # Update breakdown counts
            breakdown = dict(match_eval.scoring_breakdown)
            if req.is_mandatory:
                breakdown["mandatory_matched"] = breakdown.get("mandatory_matched", 0) + 1
                total = breakdown.get("mandatory_total", 1)
                breakdown["mandatory_coverage_ratio"] = round(
                    breakdown["mandatory_matched"] / total, 2
                )
            else:
                breakdown["preferred_matched"] = breakdown.get("preferred_matched", 0) + 1
                total = breakdown.get("preferred_total", 1)
                breakdown["preferred_coverage_ratio"] = round(
                    breakdown["preferred_matched"] / total, 2
                )
            match_eval.scoring_breakdown = breakdown

            await db.commit()
            await db.refresh(match_eval)

        return match_eval

    async def delete_match(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        match_id: uuid.UUID,
    ) -> bool:
        stmt = select(MatchEvaluation).where(
            MatchEvaluation.id == match_id,
            MatchEvaluation.user_id == user_id,
        )
        res = await db.execute(stmt)
        match_eval = res.scalar_one_or_none()
        if not match_eval:
            return False

        await db.delete(match_eval)
        await db.commit()
        return True


# Global matching service instance
matching_service = MatchingService()
