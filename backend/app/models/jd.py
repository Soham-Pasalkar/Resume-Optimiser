import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class JobDescription(TimestampedBase):
    __tablename__ = "job_descriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    company_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    department: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    seniority_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    work_mode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    salary_range: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    requirements: Mapped[list["JDRequirement"]] = relationship(
        "JDRequirement",
        back_populates="job_description",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class JDRequirement(TimestampedBase):
    __tablename__ = "jd_requirements"

    jd_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="technical_skill",
        nullable=False,
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    importance_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    min_years_experience: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    canonical_skill_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    job_description: Mapped["JobDescription"] = relationship(
        "JobDescription",
        back_populates="requirements",
    )
