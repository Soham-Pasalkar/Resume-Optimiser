import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.jd import JDRequirement, JobDescription
from app.modules.jd_engine.extractor import jd_extractor


class JDService:
    """Orchestrates job description analysis, decomposition, and persistent storage."""

    async def analyze_and_store(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        raw_text: str,
        custom_title: str | None = None,
        company_name: str | None = None,
    ) -> JobDescription:
        # Extract decomposed requirements and metadata
        decomposed = await jd_extractor.extract(raw_text)

        title = (
            custom_title.strip() if custom_title and custom_title.strip() else decomposed.job_title
        )
        company = (
            company_name.strip()
            if company_name and company_name.strip()
            else decomposed.company_name
        )

        jd = JobDescription(
            user_id=user_id,
            job_title=title,
            company_name=company,
            department=decomposed.department,
            seniority_level=decomposed.seniority_level,
            work_mode=decomposed.work_mode,
            location=decomposed.location,
            salary_range=decomposed.salary_range,
            raw_text=raw_text,
        )
        db.add(jd)
        await db.flush()

        for req in decomposed.requirements:
            jd_req = JDRequirement(
                jd_id=jd.id,
                requirement_text=req.requirement_text,
                category=req.category,
                is_mandatory=req.is_mandatory,
                importance_weight=req.importance_weight,
                min_years_experience=req.min_years_experience,
                canonical_skill_name=req.canonical_skill_name,
            )
            db.add(jd_req)

        await db.commit()

        # Re-fetch with eager loaded requirements
        return await self.get_jd_by_id(db, user_id, jd.id)  # type: ignore

    async def get_user_jds(self, db: AsyncSession, user_id: uuid.UUID) -> list[JobDescription]:
        stmt = (
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .order_by(JobDescription.created_at.desc())
            .options(selectinload(JobDescription.requirements))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_jd_by_id(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        jd_id: uuid.UUID,
    ) -> JobDescription | None:
        stmt = (
            select(JobDescription)
            .where(JobDescription.id == jd_id, JobDescription.user_id == user_id)
            .options(selectinload(JobDescription.requirements))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_jd(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        jd_id: uuid.UUID,
    ) -> bool:
        jd = await self.get_jd_by_id(db, user_id, jd_id)
        if not jd:
            return False
        await db.delete(jd)
        await db.commit()
        return True


# Global service instance
jd_service = JDService()
