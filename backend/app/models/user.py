import uuid
from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, TimestampedBase


class User(TimestampedBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # 1-to-1 Relationship with UserProfile
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class UserProfile(TimestampedBase):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    headline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    target_role_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    target_seniority: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    years_of_experience: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    linkedin_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    github_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    portfolio_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    preferences: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )
