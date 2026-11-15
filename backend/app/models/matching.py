import uuid

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class MatchEvaluation(TimestampedBase):
    __tablename__ = "match_evaluations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    jd_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    lexical_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    semantic_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    skill_match_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    experience_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    domain_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    scoring_breakdown: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    summary_analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    gap_items: Mapped[list["SkillGapItem"]] = relationship(
        "SkillGapItem",
        back_populates="match_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    resume = relationship("Resume", lazy="selectin")
    job_description = relationship("JobDescription", lazy="selectin")


class SkillGapItem(TimestampedBase):
    __tablename__ = "skill_gap_items"

    match_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("match_evaluations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("jd_requirements.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # DEMONSTRATED, PARTIAL, NOT_DEMONSTRATED, REQUIRES_VERIFICATION
    gap_severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # CRITICAL, MODERATE, LOW
    evidence_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    similarity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    suggested_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    match_evaluation: Mapped["MatchEvaluation"] = relationship(
        "MatchEvaluation",
        back_populates="gap_items",
    )
    requirement = relationship("JDRequirement", lazy="selectin")
