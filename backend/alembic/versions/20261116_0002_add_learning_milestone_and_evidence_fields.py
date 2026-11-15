"""add learning milestone and evidence verification fields

Revision ID: 20261116_0002
Revises: 20261114_0001
Create Date: 2026-11-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20261116_0002"
down_revision: Union[str, None] = "20261114_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("learning_milestones") as batch_op:
        batch_op.add_column(sa.Column("why_it_matters", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("prerequisites", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("learning_objectives", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("practical_exercises", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("expected_deliverables", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("verification_criteria", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("estimated_hours", sa.Integer(), nullable=False, server_default="10"))
        batch_op.add_column(sa.Column("completed_evidence", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("evidence_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="UNSUBMITTED"))


def downgrade() -> None:
    with op.batch_alter_table("learning_milestones") as batch_op:
        batch_op.drop_column("verification_status")
        batch_op.drop_column("evidence_verified")
        batch_op.drop_column("completed_evidence")
        batch_op.drop_column("estimated_hours")
        batch_op.drop_column("verification_criteria")
        batch_op.drop_column("expected_deliverables")
        batch_op.drop_column("practical_exercises")
        batch_op.drop_column("learning_objectives")
        batch_op.drop_column("prerequisites")
        batch_op.drop_column("why_it_matters")
