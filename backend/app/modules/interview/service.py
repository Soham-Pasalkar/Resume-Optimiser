import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.career import InterviewPrep, InterviewQuestion
from app.models.matching import MatchEvaluation
from app.modules.interview.evaluator import answer_evaluator
from app.modules.interview.prompt_generator import interview_prompt_generator


class InterviewService:
    """Manages interview prep generation, question bank queries, and mock answer evaluations."""

    async def create_interview_prep(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        match_evaluation_id: uuid.UUID,
    ) -> InterviewPrep:
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

        target_role = (
            match_eval.job_description.job_title
            if match_eval.job_description
            else "Software Engineer"
        )
        company = match_eval.job_description.company_name if match_eval.job_description else None

        # Generate questions
        questions_data = await interview_prompt_generator.generate_questions(match_eval)

        prep = InterviewPrep(
            user_id=user_id,
            match_evaluation_id=match_eval.id,
            target_role_title=target_role,
            company_name=company,
        )
        db.add(prep)
        await db.flush()

        for q in questions_data:
            question = InterviewQuestion(
                prep_id=prep.id,
                question_type=q.get("question_type", "TECHNICAL"),
                question_text=q.get("question_text", ""),
                target_skill_or_gap=q.get("target_skill_or_gap"),
                evaluation_criteria=q.get("evaluation_criteria", ""),
                star_guidelines=q.get("star_guidelines", {}),
            )
            db.add(question)

        await db.commit()
        return await self.get_interview_prep(db, user_id, prep.id)  # type: ignore

    async def get_interview_prep(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        prep_id: uuid.UUID,
    ) -> InterviewPrep | None:
        stmt = (
            select(InterviewPrep)
            .where(InterviewPrep.id == prep_id, InterviewPrep.user_id == user_id)
            .options(selectinload(InterviewPrep.questions))
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_interview_preps(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[InterviewPrep]:
        stmt = (
            select(InterviewPrep)
            .where(InterviewPrep.user_id == user_id)
            .order_by(InterviewPrep.created_at.desc())
            .options(selectinload(InterviewPrep.questions))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def evaluate_answer(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        question_id: uuid.UUID,
        candidate_response: str,
    ) -> InterviewQuestion:
        stmt = (
            select(InterviewQuestion)
            .join(InterviewPrep, InterviewQuestion.prep_id == InterviewPrep.id)
            .where(InterviewQuestion.id == question_id, InterviewPrep.user_id == user_id)
            .options(selectinload(InterviewQuestion.prep))
        )
        res = await db.execute(stmt)
        question = res.scalar_one_or_none()
        if not question:
            raise ValueError("Interview question not found.")

        # Run evaluation
        feedback = await answer_evaluator.evaluate_response(question, candidate_response)

        question.practice_response = candidate_response
        question.ai_feedback = feedback

        await db.commit()
        await db.refresh(question)
        return question

    async def delete_interview_prep(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        prep_id: uuid.UUID,
    ) -> bool:
        stmt = select(InterviewPrep).where(
            InterviewPrep.id == prep_id,
            InterviewPrep.user_id == user_id,
        )
        res = await db.execute(stmt)
        prep = res.scalar_one_or_none()
        if not prep:
            return False

        await db.delete(prep)
        await db.commit()
        return True


# Global interview service instance
interview_service = InterviewService()
