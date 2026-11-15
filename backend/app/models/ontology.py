from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedBase


class SkillOntologyNode(TimestampedBase):
    __tablename__ = "skill_ontology_nodes"

    canonical_name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    aliases: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    parent_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
