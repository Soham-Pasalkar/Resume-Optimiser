import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class TailoredResume(TimestampedBase):
    __tablename__ = "tailored_resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_resume_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_jd_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    match_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("match_evaluations.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    tailored_content: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    pdf_export_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    docx_export_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    # Relationships
    diffs: Mapped[list["TailoredBulletDiff"]] = relationship(
        "TailoredBulletDiff",
        back_populates="tailored_resume",
        cascade="all, delete-orphan",
        order_by="TailoredBulletDiff.created_at",
        lazy="selectin",
    )
    source_resume = relationship("Resume", lazy="selectin")
    target_jd = relationship("JobDescription", lazy="selectin")


class TailoredBulletDiff(TimestampedBase):
    __tablename__ = "tailored_bullet_diffs"

    tailored_resume_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("tailored_resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    section_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    item_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    bullet_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    original_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    optimized_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    targeted_requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("jd_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    nli_verification_status: Mapped[str] = mapped_column(
        String(50),
        default="ENTAILMENT",
        nullable=False,
    )  # ENTAILMENT, NEUTRAL, FLAGGED
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )  # PENDING, ACCEPTED, REJECTED, EDITED
    edited_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    tailored_resume: Mapped["TailoredResume"] = relationship(
        "TailoredResume",
        back_populates="diffs",
    )
    targeted_requirement = relationship("JDRequirement", lazy="selectin")
