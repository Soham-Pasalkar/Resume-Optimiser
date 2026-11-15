import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.career import LearningMilestone, LearningRoadmap
from app.models.matching import MatchEvaluation
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

        # Identify unresolved gaps
        unresolved_gaps = [
            g for g in match_eval.gap_items if not g.is_resolved and g.status != "DEMONSTRATED"
        ]

        target_role = (
            match_eval.job_description.job_title if match_eval.job_description else "Target Role"
        )

        # Generate roadmap data
        roadmap_data = await roadmap_generator.generate_roadmap(
            target_role=target_role,
            unresolved_gaps=unresolved_gaps,
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
        """Submit completed portfolio deliverable evidence, mark milestone complete, and sync verified skill."""
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

        milestone.completed_evidence = evidence
        milestone.is_completed = True
        milestone.evidence_verified = True

        # Check if all completed
        roadmap = milestone.roadmap
        all_done = all(
            m.is_completed if m.id != milestone.id else True for m in roadmap.milestones
        )
        roadmap.status = "COMPLETED" if all_done else "ACTIVE"

        # Auto-sync to Candidate Profile Skills
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
        else:
            new_skill = CandidateSkill(
                user_id=user_id,
                skill_name=canonical_name,
                normalized_name=norm_name,
                category=category if category != "Other" else "Verified Project Competencies",
                proficiency_level="proficient",
                is_user_verified=True,
            )
            db.add(new_skill)

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
