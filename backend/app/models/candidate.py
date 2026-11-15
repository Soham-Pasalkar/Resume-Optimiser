import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, TimestampedBase


class CandidateSkill(TimestampedBase):
    __tablename__ = "candidate_skills"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    proficiency_level: Mapped[str | None] = mapped_column(
        String(50),
        default="proficient",
        nullable=True,
    )
    years_experience: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    evidence_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    evidence_item_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_user_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
