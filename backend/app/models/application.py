import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class JobApplication(TimestampedBase):
    __tablename__ = "job_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("job_descriptions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    tailored_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("tailored_resumes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    match_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("match_evaluations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    stage: Mapped[str] = mapped_column(
        String(50),
        default="WISHLIST",
        nullable=False,
    )  # WISHLIST, APPLIED, SCREENING, INTERVIEWING, OFFER, REJECTED, WITHDRAWN
    priority: Mapped[str] = mapped_column(
        String(20),
        default="MEDIUM",
        nullable=False,
    )  # HIGH, MEDIUM, LOW
    salary_range: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    job_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    applied_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    job_description = relationship("JobDescription", lazy="selectin")
    tailored_resume = relationship("TailoredResume", lazy="selectin")
    match_evaluation = relationship("MatchEvaluation", lazy="selectin")

    activities: Mapped[list["ApplicationActivity"]] = relationship(
        "ApplicationActivity",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationActivity.created_at.desc()",
        lazy="selectin",
    )


class ApplicationActivity(TimestampedBase):
    __tablename__ = "application_activities"

    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # STAGE_CHANGE, NOTE_ADDED, CREATED, UPDATED
    from_stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    to_stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationship
    application: Mapped["JobApplication"] = relationship(
        "JobApplication",
        back_populates="activities",
    )
