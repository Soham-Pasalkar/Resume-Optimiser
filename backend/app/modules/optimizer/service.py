import copy
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.models.jd import JobDescription
from app.models.optimizer import TailoredBulletDiff, TailoredResume
from app.models.resume import Resume, ResumeSection
from app.models.user import User
from app.modules.candidate.service import candidate_service
from app.modules.matching.dense import dense_matcher
from app.modules.optimizer.exporter import resume_exporter
from app.modules.optimizer.rewriter import bullet_rewriter


class OptimizerService:
    """Orchestrates role-specific resume tailoring, NLI-verified diff generation, and ATS document export."""

    async def create_tailored_resume(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        jd_id: uuid.UUID,
    ) -> TailoredResume:
        # 1. Fetch source resume
        resume_stmt = (
            select(Resume)
            .where(Resume.id == resume_id, Resume.user_id == user_id)
            .options(selectinload(Resume.sections).selectinload(ResumeSection.items))
        )
        resume_res = await db.execute(resume_stmt)
        resume = resume_res.scalar_one_or_none()
        if not resume:
            raise ValueError("Source resume not found.")

        # 2. Fetch target JD
        jd_stmt = (
            select(JobDescription)
            .where(JobDescription.id == jd_id, JobDescription.user_id == user_id)
            .options(selectinload(JobDescription.requirements))
        )
        jd_res = await db.execute(jd_stmt)
        jd = jd_res.scalar_one_or_none()
        if not jd:
            raise ValueError("Target job description not found.")

        # 3. Fetch user info for factual candidate identity
        user_stmt = select(User).where(User.id == user_id).options(selectinload(User.profile))
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        candidate_name = user.full_name.strip() if (user and user.full_name) else "Candidate Profile"

        contact_parts = []
        if user and user.email:
            contact_parts.append(user.email)
        if user and user.profile:
            if user.profile.headline:
                contact_parts.append(user.profile.headline)
            if user.profile.linkedin_url:
                contact_parts.append(user.profile.linkedin_url)
            if user.profile.github_url:
                contact_parts.append(user.profile.github_url)
        if not contact_parts:
            contact_parts = ["Candidate Profile Verified | CareerPilot Intelligence Platform"]
        contact_info = " • ".join(contact_parts)

        # 4. Fetch candidate profile skills
        candidate_skills = await candidate_service.get_profile(db, user_id)

        # Target JD ontology skills for prioritization
        target_skills = {
            (r.canonical_skill_name or "").lower()
            for r in jd.requirements
            if r.canonical_skill_name
        }

        # 5. Build initial snapshot of tailored content with skills section prioritization
        sections_snapshot = []
        for sec in resume.sections:
            sec_type = (sec.section_type or "").lower()
            heading = (sec.heading or "").lower()
            items_snapshot = []
            for item in sec.items:
                items_snapshot.append(
                    {
                        "id": str(item.id),
                        "title": item.title,
                        "organization": item.organization,
                        "location": item.location,
                        "start_date": item.start_date,
                        "end_date": item.end_date,
                        "is_current": item.is_current,
                        "bullets": list(item.bullets or []),
                    }
                )

            # In Skills sections, prioritize skills that match target job requirements
            raw_content = sec.raw_content
            if ("skill" in sec_type or "skill" in heading) and raw_content:
                lines = [ln.strip() for ln in raw_content.splitlines() if ln.strip()]
                relevant = [ln for ln in lines if any(ts in ln.lower() for ts in target_skills)]
                other = [ln for ln in lines if not any(ts in ln.lower() for ts in target_skills)]
                if relevant:
                    raw_content = "\n".join(relevant + other)

            sections_snapshot.append(
                {
                    "id": str(sec.id),
                    "section_type": sec.section_type,
                    "heading": sec.heading,
                    "raw_content": raw_content,
                    "display_order": sec.display_order,
                    "items": items_snapshot,
                }
            )

        tailored_content = {
            "candidate_name": candidate_name,
            "full_name": candidate_name,
            "contact_info": contact_info,
            "sections": sections_snapshot,
        }

        # 6. Create TailoredResume record
        version_title = f"Tailored for {jd.job_title} at {jd.company_name or 'Target Role'}"
        tailored = TailoredResume(
            user_id=user_id,
            source_resume_id=resume.id,
            target_jd_id=jd.id,
            version_title=version_title,
            tailored_content=tailored_content,
        )
        db.add(tailored)
        await db.flush()

        # 7. Generate tailored diffs with genuine semantic requirement mapping
        for sec in resume.sections:
            sec_type = sec.section_type.lower()
            if (
                "experience" not in sec_type
                and "work" not in sec_type
                and "project" not in sec_type
            ):
                continue

            for item in sec.items:
                for b_idx, bullet in enumerate(item.bullets or []):
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    if len(bullet_text.strip()) < 15:
                        continue

                    # Evaluate bullet against all requirements to find genuinely aligned target
                    bullet_lower = bullet_text.lower()
                    best_req = None
                    best_sim = 0.0

                    for req in jd.requirements:
                        canonical = (req.canonical_skill_name or "").lower()
                        sim = 0.0
                        if canonical and canonical in bullet_lower:
                            sim = 0.85
                        else:
                            sim, _ = await dense_matcher.find_best_evidence_match(
                                req.requirement_text, [bullet_text]
                            )

                        if sim > best_sim:
                            best_sim = sim
                            best_req = req

                    # Only link to requirement if similarity meets threshold, otherwise rewrite for role
                    target_req = best_req if best_sim >= 0.45 else None

                    rewrite_result = await bullet_rewriter.rewrite_bullet(
                        original_text=bullet_text,
                        jd=jd,
                        candidate_skills=candidate_skills,
                        target_requirement=target_req,
                    )

                    diff = TailoredBulletDiff(
                        tailored_resume_id=tailored.id,
                        section_id=str(sec.id),
                        item_id=str(item.id),
                        bullet_index=b_idx,
                        original_text=rewrite_result["original_text"],
                        optimized_text=rewrite_result["optimized_text"],
                        rationale=rewrite_result["rationale"],
                        targeted_requirement_id=target_req.id if target_req else None,
                        nli_verification_status=rewrite_result.get(
                            "nli_verification_status", "ENTAILMENT"
                        ),
                        status="PENDING",
                    )
                    db.add(diff)

        await db.commit()
        return await self.get_tailored_resume(db, user_id, tailored.id)  # type: ignore

    async def get_tailored_resume(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
    ) -> TailoredResume | None:
        stmt = (
            select(TailoredResume)
            .where(TailoredResume.id == tailored_id, TailoredResume.user_id == user_id)
            .options(
                selectinload(TailoredResume.diffs),
                selectinload(TailoredResume.source_resume),
                selectinload(TailoredResume.target_jd),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_tailored_resumes(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[TailoredResume]:
        stmt = (
            select(TailoredResume)
            .where(TailoredResume.user_id == user_id)
            .order_by(TailoredResume.created_at.desc())
            .options(
                selectinload(TailoredResume.source_resume),
                selectinload(TailoredResume.target_jd),
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_diff_status(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        diff_id: uuid.UUID,
        new_status: str,
        edited_text: str | None = None,
    ) -> TailoredBulletDiff:
        # Fetch diff with parent tailored resume
        stmt = (
            select(TailoredBulletDiff)
            .join(TailoredResume, TailoredBulletDiff.tailored_resume_id == TailoredResume.id)
            .where(TailoredBulletDiff.id == diff_id, TailoredResume.user_id == user_id)
            .options(selectinload(TailoredBulletDiff.tailored_resume))
        )
        res = await db.execute(stmt)
        diff = res.scalar_one_or_none()
        if not diff:
            raise ValueError("Diff not found or unauthorized.")

        diff.status = new_status
        if edited_text is not None:
            diff.edited_text = edited_text.strip()

        # Update tailored_content snapshot
        tailored = diff.tailored_resume
        content = copy.deepcopy(tailored.tailored_content)

        # Resolve active text for this bullet
        active_text = diff.original_text
        if new_status == "ACCEPTED":
            active_text = diff.optimized_text
        elif new_status == "EDITED" and diff.edited_text:
            active_text = diff.edited_text
        elif new_status == "REJECTED":
            active_text = diff.original_text

        # Locate section and item in snapshot
        updated = False
        for sec in content.get("sections", []):
            if diff.section_id and sec.get("id") == diff.section_id:
                for item in sec.get("items", []):
                    if diff.item_id and item.get("id") == diff.item_id:
                        bullets = item.get("bullets", [])
                        if 0 <= diff.bullet_index < len(bullets):
                            bullets[diff.bullet_index] = active_text
                            item["bullets"] = bullets
                            updated = True
                            break
            if not updated:
                # Match by original text
                for item in sec.get("items", []):
                    bullets = item.get("bullets", [])
                    for i, b in enumerate(bullets):
                        if b == diff.original_text:
                            bullets[i] = active_text
                            item["bullets"] = bullets
                            updated = True
                            break

        tailored.tailored_content = content
        flag_modified(tailored, "tailored_content")
        await db.commit()
        await db.refresh(tailored)
        await db.refresh(diff)
        return diff

    async def export_pdf(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
    ) -> bytes:
        tailored = await self.get_tailored_resume(db, user_id, tailored_id)
        if not tailored:
            raise ValueError("Tailored resume not found.")
        return resume_exporter.generate_pdf(tailored.tailored_content)

    async def export_docx(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
    ) -> bytes:
        tailored = await self.get_tailored_resume(db, user_id, tailored_id)
        if not tailored:
            raise ValueError("Tailored resume not found.")
        return resume_exporter.generate_docx(tailored.tailored_content)

    async def delete_tailored_resume(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
    ) -> bool:
        stmt = select(TailoredResume).where(
            TailoredResume.id == tailored_id,
            TailoredResume.user_id == user_id,
        )
        res = await db.execute(stmt)
        tailored = res.scalar_one_or_none()
        if not tailored:
            return False

        await db.delete(tailored)
        await db.commit()
        return True


# Global optimizer service instance
optimizer_service = OptimizerService()
