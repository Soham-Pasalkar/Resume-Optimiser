import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import ApplicationActivity, JobApplication
from app.models.jd import JobDescription
from app.models.matching import MatchEvaluation
from app.schemas.application import (
    JobApplicationCreate,
    JobApplicationUpdate,
    OpportunityComparisonItem,
    OpportunityComparisonResponse,
)


class ApplicationService:
    """Manages job application lifecycle, kanban board state transitions, activity logging, and opportunity comparison."""

    async def create_application(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        payload: JobApplicationCreate,
    ) -> JobApplication:
        # Resolve company/title from JD if provided
        company_name = payload.company_name
        job_title = payload.job_title

        if payload.job_description_id:
            jd_stmt = select(JobDescription).where(
                JobDescription.id == payload.job_description_id,
                JobDescription.user_id == user_id,
            )
            jd_res = await db.execute(jd_stmt)
            jd = jd_res.scalar_one_or_none()
            if jd:
                if not company_name and jd.company_name:
                    company_name = jd.company_name
                if not job_title and jd.job_title:
                    job_title = jd.job_title

        app = JobApplication(
            user_id=user_id,
            company_name=company_name,
            job_title=job_title,
            job_description_id=payload.job_description_id,
            tailored_resume_id=payload.tailored_resume_id,
            match_evaluation_id=payload.match_evaluation_id,
            location=payload.location,
            stage=payload.stage.upper(),
            priority=payload.priority.upper(),
            salary_range=payload.salary_range,
            job_url=payload.job_url,
            applied_date=payload.applied_date,
            deadline=payload.deadline,
            notes=payload.notes,
            is_archived=False,
        )
        db.add(app)
        await db.flush()

        # Log creation activity
        activity = ApplicationActivity(
            application_id=app.id,
            activity_type="CREATED",
            to_stage=app.stage,
            note="Application record created.",
        )
        db.add(activity)

        await db.commit()
        return await self.get_application(db, user_id, app.id)  # type: ignore

    async def get_application(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> JobApplication | None:
        stmt = (
            select(JobApplication)
            .where(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id,
            )
            .options(
                selectinload(JobApplication.job_description),
                selectinload(JobApplication.tailored_resume),
                selectinload(JobApplication.match_evaluation).selectinload(
                    MatchEvaluation.gap_items
                ),
                selectinload(JobApplication.activities),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_applications(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        stage: str | None = None,
        include_archived: bool = False,
        search: str | None = None,
    ) -> list[JobApplication]:
        stmt = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id)
            .options(
                selectinload(JobApplication.match_evaluation),
                selectinload(JobApplication.tailored_resume),
                selectinload(JobApplication.activities),
            )
            .order_by(JobApplication.created_at.desc())
        )

        if not include_archived:
            stmt = stmt.where(JobApplication.is_archived.is_(False))

        if stage and stage.upper() != "ALL":
            stmt = stmt.where(JobApplication.stage == stage.upper())

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                (JobApplication.company_name.ilike(search_pattern))
                | (JobApplication.job_title.ilike(search_pattern))
            )

        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_application(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        payload: JobApplicationUpdate,
    ) -> JobApplication:
        app = await self.get_application(db, user_id, application_id)
        if not app:
            raise ValueError("Job application not found.")

        old_stage = app.stage
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "stage" and value:
                value = value.upper()
            if field == "priority" and value:
                value = value.upper()
            setattr(app, field, value)

        # Log stage change if stage was updated
        if "stage" in update_data and update_data["stage"] != old_stage:
            activity = ApplicationActivity(
                application_id=app.id,
                activity_type="STAGE_CHANGE",
                from_stage=old_stage,
                to_stage=app.stage,
                note=f"Application stage updated from {old_stage} to {app.stage}.",
            )
            db.add(activity)

        await db.commit()
        return await self.get_application(db, user_id, app.id)  # type: ignore

    async def update_application_stage(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        new_stage: str,
        note: str | None = None,
    ) -> JobApplication:
        app = await self.get_application(db, user_id, application_id)
        if not app:
            raise ValueError("Job application not found.")

        old_stage = app.stage
        new_stage = new_stage.upper()

        if old_stage != new_stage:
            app.stage = new_stage
            activity = ApplicationActivity(
                application_id=app.id,
                activity_type="STAGE_CHANGE",
                from_stage=old_stage,
                to_stage=new_stage,
                note=note or f"Stage transitioned to {new_stage}.",
            )
            db.add(activity)
            await db.commit()

        return await self.get_application(db, user_id, app.id)  # type: ignore

    async def delete_application(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> bool:
        stmt = select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == user_id,
        )
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()
        if not app:
            return False

        await db.delete(app)
        await db.commit()
        return True

    async def compare_opportunities(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        application_ids: list[uuid.UUID],
    ) -> OpportunityComparisonResponse:
        stmt = (
            select(JobApplication)
            .where(
                JobApplication.id.in_(application_ids),
                JobApplication.user_id == user_id,
            )
            .options(
                selectinload(JobApplication.match_evaluation).selectinload(
                    MatchEvaluation.gap_items
                ),
            )
        )
        res = await db.execute(stmt)
        apps = list(res.scalars().all())

        if len(apps) < 2:
            raise ValueError(
                "At least 2 matching applications belonging to current user are required for comparison."
            )

        items: list[OpportunityComparisonItem] = []
        best_app = None
        highest_score = -1.0

        for a in apps:
            eval_obj = a.match_evaluation
            overall = eval_obj.overall_score if eval_obj else None
            skill_score = eval_obj.skill_match_score if eval_obj else None
            exp_score = eval_obj.experience_score if eval_obj else None

            demonstrated = []
            missing = []

            if eval_obj and eval_obj.gap_items:
                for gap in eval_obj.gap_items:
                    skill_name = "Skill"
                    if gap.requirement:
                        skill_name = (
                            gap.requirement.canonical_skill_name
                            or gap.requirement.requirement_text[:40]
                            or "Skill"
                        )
                    if gap.status == "DEMONSTRATED":
                        demonstrated.append(skill_name)
                    elif gap.status in ("NOT_DEMONSTRATED", "PARTIAL"):
                        missing.append(skill_name)

            if overall and overall > highest_score:
                highest_score = overall
                best_app = a

            items.append(
                OpportunityComparisonItem(
                    application_id=a.id,
                    company_name=a.company_name,
                    job_title=a.job_title,
                    location=a.location,
                    stage=a.stage,
                    priority=a.priority,
                    salary_range=a.salary_range,
                    overall_match_score=overall,
                    skill_match_score=skill_score,
                    experience_score=exp_score,
                    top_demonstrated_skills=demonstrated[:6],
                    critical_missing_skills=missing[:6],
                )
            )

        if best_app and highest_score > 0:
            summary = (
                f"Based on comparative hybrid scoring, '{best_app.job_title}' at {best_app.company_name} "
                f"demonstrates the strongest profile alignment with an overall match score of {round(highest_score, 1)}%. "
                f"Prioritize tailoring targeted project evidence for high-priority pipeline opportunities."
            )
        else:
            summary = (
                f"Comparing {len(apps)} pipeline opportunities across stages. "
                "Ensure tailored resumes and match reports are attached for quantitative qualification benchmarking."
            )

        return OpportunityComparisonResponse(
            opportunities=items,
            comparison_summary=summary,
        )


application_service = ApplicationService()
