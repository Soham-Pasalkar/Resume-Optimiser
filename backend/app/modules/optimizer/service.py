import copy
import uuid
from typing import Any

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
from app.modules.optimizer.ats_scorer import ats_evaluator
from app.modules.optimizer.composer import resume_composer
from app.modules.optimizer.exporter import resume_exporter
from app.modules.optimizer.intelligence import content_intelligence
from app.modules.optimizer.rewriter import bullet_rewriter


class OptimizerService:
    """Orchestrates role-specific resume tailoring, requirement-to-evidence mapping,
    layered factual verification, dynamic composition IR, and ATS document export.
    """

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

        # 3. Fetch candidate user & profile info for factual candidate identity
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

        # 5. Run Content Intelligence & Requirement-to-Evidence Mapping
        intel_results = await content_intelligence.analyze_and_map(
            resume=resume,
            jd=jd,
            candidate_skills=candidate_skills,
        )

        req_mappings = intel_results.get("requirement_mappings", [])
        missing_reqs = intel_results.get("missing_requirements", [])
        content_decisions = intel_results.get("content_decisions", [])

        # Index mapped requirements by (section_id, item_id, bullet_index)
        mapped_req_by_bullet: dict[tuple[str, str, int], dict[str, Any]] = {}
        req_by_id = {r.id: r for r in jd.requirements}
        for rm in req_mappings:
            sec_id = rm.get("matched_section_id") or ""
            itm_id = rm.get("matched_item_id") or ""
            b_idx = rm.get("matched_bullet_index")
            if b_idx is not None:
                mapped_req_by_bullet[(sec_id, itm_id, b_idx)] = rm

        # 6. Target JD ontology skills for prioritization in skills sections
        target_skills = {
            (r.canonical_skill_name or "").lower()
            for r in jd.requirements
            if r.canonical_skill_name
        }

        # 7. Build initial snapshot of sections
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
                    "is_included": True,
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
            "raw_sections": sections_snapshot,
            "requirement_mappings": req_mappings,
            "missing_requirements": missing_reqs,
            "content_decisions": content_decisions,
            "intel_summary": intel_results.get("summary", {}),
        }

        # 8. Create TailoredResume record
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

        # 9. Generate tailored diffs for experience and project bullets
        created_diffs: list[TailoredBulletDiff] = []
        for sec in resume.sections:
            sec_type = (sec.section_type or "").lower()
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

                    # Check if requirement mapping already associated a requirement
                    sec_key = (str(sec.id), str(item.id), b_idx)
                    target_req = None
                    if sec_key in mapped_req_by_bullet:
                        req_uuid_str = mapped_req_by_bullet[sec_key]["requirement_id"]
                        target_req = req_by_id.get(uuid.UUID(req_uuid_str))

                    if not target_req:
                        # Find best semantic requirement if similarity meets threshold
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
                    created_diffs.append(diff)

        # 10. Re-sync content snapshot via resume_composer
        synced = resume_composer.sync_tailored_content_snapshot(tailored, created_diffs)
        # Preserve intelligence metadata
        synced["requirement_mappings"] = req_mappings
        synced["missing_requirements"] = missing_reqs
        synced["content_decisions"] = content_decisions
        synced["intel_summary"] = intel_results.get("summary", {})
        synced["four_tier_breakdown"] = intel_results.get("four_tier_breakdown", {})
        synced["role_summary"] = intel_results.get("role_summary", "")

        # Compute initial ATS metrics
        ats_comp = ats_evaluator.evaluate_job_compatibility(synced, jd, req_mappings)
        ats_read = ats_evaluator.evaluate_ats_readability(synced)
        synced["ats_analysis"] = {
            "job_compatibility": ats_comp,
            "ats_readability": ats_read,
        }

        tailored.tailored_content = synced
        flag_modified(tailored, "tailored_content")

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
                selectinload(TailoredResume.target_jd).selectinload(JobDescription.requirements),
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
                selectinload(TailoredResume.diffs),
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
            .options(
                selectinload(TailoredBulletDiff.tailored_resume).selectinload(
                    TailoredResume.diffs
                )
            )
        )
        res = await db.execute(stmt)
        diff = res.scalar_one_or_none()
        if not diff:
            raise ValueError("Diff not found or unauthorized.")

        # Update status
        diff.status = new_status
        if new_status == "RESTORED":
            diff.status = "REJECTED"
            diff.edited_text = None
        elif edited_text is not None:
            diff.edited_text = edited_text.strip()

        # Update tailored_content snapshot using resume_composer
        tailored = diff.tailored_resume
        existing_intel = {
            "requirement_mappings": tailored.tailored_content.get("requirement_mappings", []),
            "missing_requirements": tailored.tailored_content.get("missing_requirements", []),
            "content_decisions": tailored.tailored_content.get("content_decisions", []),
            "intel_summary": tailored.tailored_content.get("intel_summary", {}),
            "four_tier_breakdown": tailored.tailored_content.get("four_tier_breakdown", {}),
            "role_summary": tailored.tailored_content.get("role_summary", ""),
            "ats_analysis": tailored.tailored_content.get("ats_analysis", {}),
        }

        synced = resume_composer.sync_tailored_content_snapshot(tailored, tailored.diffs)
        synced.update(existing_intel)
        tailored.tailored_content = synced
        flag_modified(tailored, "tailored_content")

        await db.commit()
        await db.refresh(tailored)
        await db.refresh(diff)
        return diff

    async def restore_diff_to_original(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        diff_id: uuid.UUID,
    ) -> TailoredBulletDiff:
        """Explicitly restore a diff bullet to its original text."""
        return await self.update_diff_status(
            db=db,
            user_id=user_id,
            diff_id=diff_id,
            new_status="REJECTED",
            edited_text=None,
        )

    async def update_section_visibility(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
        section_id: str,
        is_included: bool,
        display_order: int | None = None,
    ) -> TailoredResume:
        """Toggle section inclusion and/or update display order in the tailored snapshot."""
        tailored = await self.get_tailored_resume(db, user_id, tailored_id)
        if not tailored:
            raise ValueError("Tailored resume not found.")

        content = copy.deepcopy(tailored.tailored_content)
        raw_secs = content.get("raw_sections", content.get("sections", []))

        for sec in raw_secs:
            if str(sec.get("id")) == str(section_id):
                sec["is_included"] = is_included
                if display_order is not None:
                    sec["display_order"] = display_order

        content["raw_sections"] = raw_secs
        tailored.tailored_content = content

        synced = resume_composer.sync_tailored_content_snapshot(tailored, tailored.diffs)
        # Preserve intelligence metadata
        for k in [
            "requirement_mappings",
            "missing_requirements",
            "content_decisions",
            "intel_summary",
            "four_tier_breakdown",
            "role_summary",
            "ats_analysis",
        ]:
            if k in content:
                synced[k] = content[k]

        tailored.tailored_content = synced
        flag_modified(tailored, "tailored_content")

        await db.commit()
        await db.refresh(tailored)
        return tailored

    async def get_ats_analysis(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Compute full ATS compatibility and readability audit with actual PDF byte extraction."""
        tailored = await self.get_tailored_resume(db, user_id, tailored_id)
        if not tailored:
            raise ValueError("Tailored resume not found.")

        content = tailored.tailored_content or {}
        jd = tailored.target_jd
        if not jd:
            raise ValueError("Target job description not found.")

        # Generate live PDF bytes to run byte-level verification
        pdf_bytes = resume_exporter.generate_pdf(content)
        comp = ats_evaluator.evaluate_job_compatibility(
            tailored_content=content,
            jd=jd,
            requirement_mappings=content.get("requirement_mappings", []),
        )
        read = ats_evaluator.evaluate_ats_readability(
            tailored_content=content,
            document_bytes=pdf_bytes,
            file_format="pdf",
        )
        return {
            "job_compatibility": comp,
            "ats_readability": read,
        }

    async def add_custom_evidence(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
        requirement_id: uuid.UUID,
        evidence_text: str,
        section_name: str = "Master Profile Evidence",
        match_category: str = "DEMONSTRATED",
    ) -> TailoredResume:
        """Manually attach candidate-verified evidence to a requirement, upgrading its tier."""
        tailored = await self.get_tailored_resume(db, user_id, tailored_id)
        if not tailored:
            raise ValueError("Tailored resume not found.")

        content = copy.deepcopy(tailored.tailored_content or {})
        req_mappings = content.get("requirement_mappings", [])
        missing_reqs = content.get("missing_requirements", [])
        four_tier = content.get("four_tier_breakdown", {})

        req_str = str(requirement_id)
        target_req = next((r for r in tailored.target_jd.requirements if str(r.id) == req_str), None)
        if not target_req:
            raise ValueError("Target requirement not found in job description.")

        # Remove from missing requirements list
        content["missing_requirements"] = [m for m in missing_reqs if m.get("requirement_id") != req_str]

        # Update or create mapping
        found_mapping = next((m for m in req_mappings if m.get("requirement_id") == req_str), None)
        if found_mapping:
            found_mapping["match_category"] = match_category
            found_mapping["original_evidence_text"] = evidence_text
            found_mapping["explanation"] = f"Candidate verified evidence: {evidence_text}"
            found_mapping["confidence_score"] = 0.95
            found_mapping["verification_status"] = "CANDIDATE_VERIFIED"
            found_mapping["requires_human_verification"] = False
        else:
            new_mapping = {
                "requirement_id": req_str,
                "requirement_text": target_req.requirement_text,
                "is_mandatory": target_req.is_mandatory,
                "canonical_skill_name": target_req.canonical_skill_name,
                "category": target_req.category,
                "matched_section_id": None,
                "matched_section_name": section_name,
                "matched_item_id": None,
                "matched_bullet_index": None,
                "original_evidence_text": evidence_text,
                "matching_method": "CANDIDATE_VERIFIED_INPUT",
                "confidence_score": 0.95,
                "verification_status": "CANDIDATE_VERIFIED",
                "match_category": match_category,
                "explanation": f"Candidate verified evidence: {evidence_text}",
                "requires_human_verification": False,
                "suggested_action": None,
            }
            req_mappings.append(new_mapping)

        content["requirement_mappings"] = req_mappings

        # Re-partition four_tier_breakdown
        four_tier["DEMONSTRATED"] = [m for m in req_mappings if m.get("match_category") == "DEMONSTRATED"]
        four_tier["TRANSFERABLE"] = [m for m in req_mappings if m.get("match_category") == "TRANSFERABLE"]
        four_tier["PROFILE_LISTED"] = [m for m in req_mappings if m.get("match_category") == "PROFILE_LISTED"]
        four_tier["MISSING"] = content["missing_requirements"]
        content["four_tier_breakdown"] = four_tier

        # Recompute ATS analysis
        comp = ats_evaluator.evaluate_job_compatibility(content, tailored.target_jd, req_mappings)
        read = ats_evaluator.evaluate_ats_readability(content)
        content["ats_analysis"] = {
            "job_compatibility": comp,
            "ats_readability": read,
        }

        tailored.tailored_content = content
        flag_modified(tailored, "tailored_content")

        await db.commit()
        await db.refresh(tailored)
        return tailored

    async def get_composition_ir(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tailored_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Fetch structured Intermediate Representation (IR) of tailored resume."""
        tailored = await self.get_tailored_resume(db, user_id, tailored_id)
        if not tailored:
            raise ValueError("Tailored resume not found.")

        ir = resume_composer.build_composition_ir(tailored, tailored.diffs)
        content = tailored.tailored_content or {}
        ir["requirement_mappings"] = content.get("requirement_mappings", [])
        ir["missing_requirements"] = content.get("missing_requirements", [])
        return ir

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
