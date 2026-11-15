import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class Resume(TimestampedBase):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    file_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_master: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    parsing_status: Mapped[str] = mapped_column(
        String(50),
        default="PARSED",
        nullable=False,
    )
    ocr_applied: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    sections: Mapped[list["ResumeSection"]] = relationship(
        "ResumeSection",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeSection.display_order",
        lazy="selectin",
    )


class ResumeSection(TimestampedBase):
    __tablename__ = "resume_sections"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    section_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    heading: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    raw_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    resume: Mapped["Resume"] = relationship(
        "Resume",
        back_populates="sections",
    )
    items: Mapped[list["ResumeItem"]] = relationship(
        "ResumeItem",
        back_populates="section",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ResumeItem(TimestampedBase):
    __tablename__ = "resume_items"

    section_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("resume_sections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    organization: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    start_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    end_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    bullets: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    section: Mapped["ResumeSection"] = relationship(
        "ResumeSection",
        back_populates="items",
    )
