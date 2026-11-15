import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate import CandidateSkill
from app.models.career import LearningMilestone, LearningRoadmap
from app.models.matching import MatchEvaluation
from app.models.resume import Resume, ResumeSection
from app.modules.learning.generator import roadmap_generator


class LearningService:
    """Manages personalized learning roadmaps, milestone tracking, and curriculum updates."""

    async def create_roadmap(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        match_evaluation_id: uuid.UUID,
    ) -> LearningRoadmap:
        # Fetch match evaluation
        stmt = (
            select(MatchEvaluation)
            .where(MatchEvaluation.id == match_evaluation_id, MatchEvaluation.user_id == user_id)
            .options(
                selectinload(MatchEvaluation.gap_items),
                selectinload(MatchEvaluation.job_description),
            )
        )
        res = await db.execute(stmt)
        match_eval = res.scalar_one_or_none()
        if not match_eval:
            raise ValueError("Match evaluation not found.")

        # Identify unresolved gaps and candidate context
        unresolved_gaps = [
            g for g in match_eval.gap_items if not g.is_resolved and g.status != "DEMONSTRATED"
        ]

        target_role = (
            match_eval.job_description.job_title if match_eval.job_description else "Target Role"
        )

        # Extract demonstrated and transferable skills from match evaluation
        demonstrated_skills: list[str] = []
        transferable_skills: list[str] = []
        for g in match_eval.gap_items:
            req_skill = g.requirement.canonical_skill_name or g.requirement.requirement_text if g.requirement else ""
            if not req_skill:
                continue
            if g.status == "DEMONSTRATED":
                demonstrated_skills.append(req_skill)
            elif g.status == "TRANSFERABLE":
                transferable_skills.append(req_skill)

        # Retrieve CandidateSkills from profile
        cand_skills_stmt = select(CandidateSkill).where(CandidateSkill.user_id == user_id)
        cand_skills_res = await db.execute(cand_skills_stmt)
        cand_skills = list(cand_skills_res.scalars().all())

        candidate_proficiency: dict[str, str] = {}
        for s in cand_skills:
            candidate_proficiency[s.normalized_name] = s.proficiency_level or "developing"
            if s.is_user_verified and s.skill_name not in demonstrated_skills:
                demonstrated_skills.append(s.skill_name)

        # Retrieve candidate's projects and work from active resume
        existing_projects: list[dict[str, Any]] = []
        resume_stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.is_master.desc(), Resume.created_at.desc())
            .options(selectinload(Resume.sections).selectinload(ResumeSection.items))
        )
        resume_res = await db.execute(resume_stmt)
        active_resume = resume_res.scalars().first()
        if active_resume:
            for sec in active_resume.sections:
                if sec.section_type in ("PROJECTS", "EXPERIENCE", "WORK"):
                    for item in sec.items:
                        existing_projects.append(
                            {
                                "title": item.title,
                                "organization": item.organization,
                                "bullets": item.bullets or [],
                            }
                        )

        candidate_context = {
            "demonstrated_skills": demonstrated_skills,
            "transferable_skills": transferable_skills,
            "candidate_proficiency": candidate_proficiency,
            "existing_projects": existing_projects,
            "target_role": target_role,
        }

        # Generate personalized roadmap data
        roadmap_data = await roadmap_generator.generate_roadmap(
            target_role=target_role,
            unresolved_gaps=unresolved_gaps,
            candidate_context=candidate_context,
        )

        roadmap = LearningRoadmap(
            user_id=user_id,
            match_evaluation_id=match_eval.id,
            target_role_title=target_role,
            estimated_total_hours=roadmap_data.get("estimated_total_hours", 40),
            status="ACTIVE",
        )
        db.add(roadmap)
        await db.flush()

        for m in roadmap_data.get("milestones", []):
            milestone = LearningMilestone(
                roadmap_id=roadmap.id,
                sequence_order=m.get("sequence_order", 1),
                skill_name=m.get("skill_name", "Skill"),
                milestone_title=m.get("milestone_title", "Milestone"),
                why_it_matters=m.get("why_it_matters"),
                description=m.get("description", ""),
                prerequisites=m.get("prerequisites", []),
                learning_objectives=m.get("learning_objectives", []),
                curated_resources=m.get("curated_resources", []),
                practical_exercises=m.get("practical_exercises", []),
                practical_project_brief=m.get("practical_project_brief"),
                expected_deliverables=m.get("expected_deliverables", []),
                verification_criteria=m.get("verification_criteria", []),
                estimated_hours=m.get("estimated_hours", 15),
                completed_evidence=None,
                evidence_verified=False,
                verification_status="UNSUBMITTED",
                is_completed=False,
            )
            db.add(milestone)

        await db.commit()
        return await self.get_roadmap(db, user_id, roadmap.id)  # type: ignore

    async def get_roadmap(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        roadmap_id: uuid.UUID,
    ) -> LearningRoadmap | None:
        stmt = (
            select(LearningRoadmap)
            .where(LearningRoadmap.id == roadmap_id, LearningRoadmap.user_id == user_id)
            .options(selectinload(LearningRoadmap.milestones))
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_roadmaps(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[LearningRoadmap]:
        stmt = (
            select(LearningRoadmap)
            .where(LearningRoadmap.user_id == user_id)
            .order_by(LearningRoadmap.created_at.desc())
            .options(selectinload(LearningRoadmap.milestones))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def toggle_milestone(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        milestone_id: uuid.UUID,
        is_completed: bool,
    ) -> LearningMilestone:
        stmt = (
            select(LearningMilestone)
            .join(LearningRoadmap, LearningMilestone.roadmap_id == LearningRoadmap.id)
            .where(LearningMilestone.id == milestone_id, LearningRoadmap.user_id == user_id)
            .options(
                selectinload(LearningMilestone.roadmap).selectinload(LearningRoadmap.milestones)
            )
        )
        res = await db.execute(stmt)
        milestone = res.scalar_one_or_none()
        if not milestone:
            raise ValueError("Milestone not found.")

        milestone.is_completed = is_completed

        # Check if all completed
        roadmap = milestone.roadmap
        all_done = all(
            m.is_completed if m.id != milestone.id else is_completed for m in roadmap.milestones
        )
        roadmap.status = "COMPLETED" if all_done else "ACTIVE"

        await db.commit()
        await db.refresh(milestone)
        return milestone

    async def submit_milestone_evidence(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        milestone_id: uuid.UUID,
        evidence: dict[str, Any],
    ) -> LearningMilestone:
        """Submit candidate deliverable evidence.
        Transitions milestone to PENDING_REVIEW.
        Does NOT auto-verify or mark professional proficiency until approved.
        """
        stmt = (
            select(LearningMilestone)
            .join(LearningRoadmap, LearningMilestone.roadmap_id == LearningRoadmap.id)
            .where(LearningMilestone.id == milestone_id, LearningRoadmap.user_id == user_id)
            .options(
                selectinload(LearningMilestone.roadmap).selectinload(LearningRoadmap.milestones)
            )
        )
        res = await db.execute(stmt)
        milestone = res.scalar_one_or_none()
        if not milestone:
            raise ValueError("Milestone not found.")

        # Validate URL formats
        for url_key in ("github_url", "demo_url"):
            val = evidence.get(url_key)
            if val:
                import urllib.parse
                parsed = urllib.parse.urlparse(str(val).strip())
                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    raise ValueError(f"Invalid URL for {url_key}: '{val}'. Must be a valid HTTP or HTTPS URL.")

        import datetime
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        structured_evidence = {
            "evidence_text": evidence.get("evidence_text", "").strip(),
            "github_url": evidence.get("github_url"),
            "demo_url": evidence.get("demo_url"),
            "test_results": evidence.get("test_results"),
            "submitted_at": now_iso,
            "verification_status": "PENDING_REVIEW",
            "provenance": {
                "source": "candidate_self_attestation",
                "verified_by": None,
                "verified_at": None,
                "review_status": "PENDING_REVIEW",
                "automated_checks": {
                    "url_format_valid": True,
                    "repository_inspected": False,
                    "notes": "Candidate self-attestation submitted; pending independent review.",
                },
            },
        }

        milestone.completed_evidence = structured_evidence
        milestone.verification_status = "PENDING_REVIEW"
        milestone.evidence_verified = False
        # Do not mark completed or verified until formal review approval
        milestone.is_completed = False

        # Register unverified self-attestation in Candidate Skills (distinguishable from verified skills)
        from app.models.candidate import CandidateSkill
        from app.modules.ontology.normalizer import skill_normalizer

        skill_name = milestone.skill_name
        canonical_name, category = skill_normalizer.normalize(skill_name)
        norm_name = canonical_name.lower()

        cand_skill_stmt = select(CandidateSkill).where(
            CandidateSkill.user_id == user_id,
            (CandidateSkill.normalized_name == norm_name)
            | (CandidateSkill.skill_name.ilike(skill_name)),
        )
        cand_skill_res = await db.execute(cand_skill_stmt)
        cand_skill = cand_skill_res.scalar_one_or_none()

        if cand_skill:
            # Preserve existing verification if already verified; do NOT promote unverified
            if not cand_skill.is_user_verified:
                cand_skill.evidence_text = f"[Self-Attestation - Pending Review]: {evidence.get('evidence_text', '')[:200]}"
                if not cand_skill.proficiency_level:
                    cand_skill.proficiency_level = "developing"
        else:
            new_skill = CandidateSkill(
                user_id=user_id,
                skill_name=canonical_name,
                normalized_name=norm_name,
                category=category if category != "Other" else "Self-Reported Competencies",
                proficiency_level="developing",
                evidence_text=f"[Self-Attestation - Pending Review]: {evidence.get('evidence_text', '')[:200]}",
                is_user_verified=False,
            )
            db.add(new_skill)

        await db.commit()
        await db.refresh(milestone)
        return milestone

    async def review_milestone_evidence(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        milestone_id: uuid.UUID,
        status: str,
        reviewer_notes: str | None = None,
    ) -> LearningMilestone:
        """Formal review of submitted milestone evidence:
        Only approved review transitions status to VERIFIED and marks skill verified.
        """
        clean_status = status.upper().strip()
        if clean_status not in ("VERIFIED", "REJECTED"):
            raise ValueError("Review status must be either 'VERIFIED' or 'REJECTED'.")

        stmt = (
            select(LearningMilestone)
            .join(LearningRoadmap, LearningMilestone.roadmap_id == LearningRoadmap.id)
            .where(LearningMilestone.id == milestone_id, LearningRoadmap.user_id == user_id)
            .options(
                selectinload(LearningMilestone.roadmap).selectinload(LearningRoadmap.milestones)
            )
        )
        res = await db.execute(stmt)
        milestone = res.scalar_one_or_none()
        if not milestone:
            raise ValueError("Milestone not found.")

        import datetime
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        evidence_dict = dict(milestone.completed_evidence or {})
        prov = dict(evidence_dict.get("provenance") or {})

        if clean_status == "VERIFIED":
            milestone.verification_status = "VERIFIED"
            milestone.evidence_verified = True
            milestone.is_completed = True

            prov["review_status"] = "VERIFIED"
            prov["verified_by"] = "careerpilot_reviewer"
            prov["verified_at"] = now_iso
            prov["reviewer_notes"] = reviewer_notes or "Evidence verified and approved."
            evidence_dict["provenance"] = prov
            evidence_dict["verification_status"] = "VERIFIED"
            milestone.completed_evidence = evidence_dict

            # Check if all completed in roadmap
            roadmap = milestone.roadmap
            all_done = all(
                m.is_completed if m.id != milestone.id else True for m in roadmap.milestones
            )
            roadmap.status = "COMPLETED" if all_done else "ACTIVE"

            # Sync to Candidate Profile as verified
            from app.models.candidate import CandidateSkill
            from app.modules.ontology.normalizer import skill_normalizer

            skill_name = milestone.skill_name
            canonical_name, category = skill_normalizer.normalize(skill_name)
            norm_name = canonical_name.lower()

            cand_skill_stmt = select(CandidateSkill).where(
                CandidateSkill.user_id == user_id,
                (CandidateSkill.normalized_name == norm_name)
                | (CandidateSkill.skill_name.ilike(skill_name)),
            )
            cand_skill_res = await db.execute(cand_skill_stmt)
            cand_skill = cand_skill_res.scalar_one_or_none()

            if cand_skill:
                cand_skill.is_user_verified = True
                cand_skill.proficiency_level = "proficient"
                cand_skill.evidence_text = f"[Verified Deliverable]: {evidence_dict.get('evidence_text', '')}"
            else:
                new_skill = CandidateSkill(
                    user_id=user_id,
                    skill_name=canonical_name,
                    normalized_name=norm_name,
                    category=category if category != "Other" else "Verified Project Competencies",
                    proficiency_level="proficient",
                    evidence_text=f"[Verified Deliverable]: {evidence_dict.get('evidence_text', '')}",
                    is_user_verified=True,
                )
                db.add(new_skill)
        else:  # REJECTED
            milestone.verification_status = "REJECTED"
            milestone.evidence_verified = False
            milestone.is_completed = False

            prov["review_status"] = "REJECTED"
            prov["verified_by"] = None
            prov["verified_at"] = None
            prov["reviewer_notes"] = reviewer_notes or "Evidence submission did not meet verification criteria."
            evidence_dict["provenance"] = prov
            evidence_dict["verification_status"] = "REJECTED"
            milestone.completed_evidence = evidence_dict

        await db.commit()
        await db.refresh(milestone)
        return milestone

    async def delete_roadmap(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        roadmap_id: uuid.UUID,
    ) -> bool:
        stmt = select(LearningRoadmap).where(
            LearningRoadmap.id == roadmap_id,
            LearningRoadmap.user_id == user_id,
        )
        res = await db.execute(stmt)
        roadmap = res.scalar_one_or_none()
        if not roadmap:
            return False

        await db.delete(roadmap)
        await db.commit()
        return True


# Global learning service instance
learning_service = LearningService()
