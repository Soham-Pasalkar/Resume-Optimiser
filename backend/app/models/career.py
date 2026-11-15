import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class LearningRoadmap(TimestampedBase):
    __tablename__ = "learning_roadmaps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    match_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("match_evaluations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_role_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estimated_total_hours: Mapped[int | None] = mapped_column(
        Integer,
        default=40,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
    )  # ACTIVE, COMPLETED, ARCHIVED

    # Relationships
    milestones: Mapped[list["LearningMilestone"]] = relationship(
        "LearningMilestone",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="LearningMilestone.sequence_order",
        lazy="selectin",
    )
    match_evaluation = relationship("MatchEvaluation", lazy="selectin")

    @property
    def total_milestones(self) -> int:
        return len(self.milestones) if self.milestones else 0

    @property
    def completed_count(self) -> int:
        return sum(1 for m in self.milestones if m.is_completed) if self.milestones else 0

    @property
    def milestones_count(self) -> int:
        return len(self.milestones) if self.milestones else 0


class LearningMilestone(TimestampedBase):
    __tablename__ = "learning_milestones"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("learning_roadmaps.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    milestone_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    curated_resources: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    practical_project_brief: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    roadmap: Mapped["LearningRoadmap"] = relationship(
        "LearningRoadmap",
        back_populates="milestones",
    )


class InterviewPrep(TimestampedBase):
    __tablename__ = "interview_preps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    match_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("match_evaluations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_role_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    company_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="prep",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.created_at",
        lazy="selectin",
    )
    match_evaluation = relationship("MatchEvaluation", lazy="selectin")

    @property
    def questions_count(self) -> int:
        return len(self.questions) if self.questions else 0


class InterviewQuestion(TimestampedBase):
    __tablename__ = "interview_questions"

    prep_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("interview_preps.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # TECHNICAL, BEHAVIORAL_STAR, GAP_DEFENSE
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    target_skill_or_gap: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    evaluation_criteria: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    star_guidelines: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    practice_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    ai_feedback: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    prep: Mapped["InterviewPrep"] = relationship(
        "InterviewPrep",
        back_populates="questions",
    )
