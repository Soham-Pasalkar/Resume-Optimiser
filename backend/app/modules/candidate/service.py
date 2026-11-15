import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate import CandidateSkill
from app.models.resume import Resume, ResumeSection
from app.modules.candidate.builder import candidate_profile_builder
from app.modules.ontology.normalizer import skill_normalizer


class CandidateService:
    """Manages candidate profile skills, evidence anchoring, and verification."""

    async def build_or_update_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        resume_id: uuid.UUID | None = None,
    ) -> list[CandidateSkill]:
        # 1. Resolve target resume
        resume = None
        if resume_id:
            stmt = (
                select(Resume)
                .where(Resume.id == resume_id, Resume.user_id == user_id)
                .options(
                    selectinload(Resume.sections).selectinload(ResumeSection.items),
                )
            )
            res = await db.execute(stmt)
            resume = res.scalar_one_or_none()
            if not resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume '{resume_id}' not found or does not belong to current user.",
                )
        else:
            # Try to get most recent master resume first
            stmt = (
                select(Resume)
                .where(Resume.user_id == user_id, Resume.is_master.is_(True))
                .order_by(Resume.created_at.desc())
                .options(
                    selectinload(Resume.sections).selectinload(ResumeSection.items),
                )
            )
            res = await db.execute(stmt)
            resume = res.scalar_one_or_none()

            # If no master resume, get most recently uploaded
            if not resume:
                stmt = (
                    select(Resume)
                    .where(Resume.user_id == user_id)
                    .order_by(Resume.created_at.desc())
                    .options(
                        selectinload(Resume.sections).selectinload(ResumeSection.items),
                    )
                )
                res = await db.execute(stmt)
                resume = res.scalar_one_or_none()

        if not resume:
            return await self.get_profile(db, user_id)

        # 2. Extract competencies with evidence anchors
        extracted_skills = candidate_profile_builder.extract_competencies(resume)

        # 3. Fetch existing skills for this user
        existing_skills = await self.get_profile(db, user_id)
        existing_map = {s.normalized_name: s for s in existing_skills}

        for item in extracted_skills:
            normalized = item["normalized_name"]
            if normalized in existing_map:
                existing_skill = existing_map[normalized]
                # Update evidence if not already verified and evidence was empty or improved
                if not existing_skill.is_user_verified and item.get("evidence_text"):
                    existing_skill.evidence_text = item["evidence_text"]
                    existing_skill.evidence_item_id = item["evidence_item_id"]
                    existing_skill.proficiency_level = item["proficiency_level"]
            else:
                new_skill = CandidateSkill(
                    user_id=user_id,
                    skill_name=item["skill_name"],
                    normalized_name=normalized,
                    category=item["category"],
                    proficiency_level=item["proficiency_level"],
                    evidence_text=item.get("evidence_text"),
                    evidence_item_id=item.get("evidence_item_id"),
                    is_user_verified=False,
                )
                db.add(new_skill)

        await db.commit()
        return await self.get_profile(db, user_id)

    async def get_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[CandidateSkill]:
        stmt = (
            select(CandidateSkill)
            .where(CandidateSkill.user_id == user_id)
            .order_by(CandidateSkill.category.asc(), CandidateSkill.normalized_name.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def verify_skill(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        is_verified: bool = True,
    ) -> CandidateSkill | None:
        stmt = select(CandidateSkill).where(
            CandidateSkill.id == skill_id, CandidateSkill.user_id == user_id
        )
        result = await db.execute(stmt)
        skill = result.scalar_one_or_none()
        if not skill:
            return None

        skill.is_user_verified = is_verified
        await db.commit()
        await db.refresh(skill)
        return skill

    async def add_custom_skill(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        skill_name: str,
        category: str | None = None,
        proficiency_level: str = "proficient",
        evidence_text: str | None = None,
    ) -> CandidateSkill:
        canonical, auto_category = skill_normalizer.normalize(skill_name)
        cat = category or auto_category

        # Check if already exists
        stmt = select(CandidateSkill).where(
            CandidateSkill.user_id == user_id,
            CandidateSkill.normalized_name == canonical,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_user_verified = True
            if evidence_text:
                existing.evidence_text = evidence_text
            if proficiency_level:
                existing.proficiency_level = proficiency_level
            await db.commit()
            await db.refresh(existing)
            return existing

        skill = CandidateSkill(
            user_id=user_id,
            skill_name=skill_name,
            normalized_name=canonical,
            category=cat,
            proficiency_level=proficiency_level,
            evidence_text=evidence_text,
            is_user_verified=True,
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return skill

    async def delete_skill(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
    ) -> bool:
        stmt = select(CandidateSkill).where(
            CandidateSkill.id == skill_id, CandidateSkill.user_id == user_id
        )
        result = await db.execute(stmt)
        skill = result.scalar_one_or_none()
        if not skill:
            return False

        await db.delete(skill)
        await db.commit()
        return True


# Global service instance
candidate_service = CandidateService()
