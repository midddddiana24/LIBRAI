"""add renewals and ai feedback

Revision ID: bb921a0cd347
Revises: ac82f18f4be1
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "bb921a0cd347"
down_revision: Union[str, Sequence[str], None] = "ac82f18f4be1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("borrowings", sa.Column("renewal_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "renewal_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("borrowing_id", sa.Integer(), sa.ForeignKey("borrowings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("renewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
    )
    op.create_index("ix_renewal_history_borrowing_id", "renewal_history", ["borrowing_id"])
    op.create_index("ix_renewal_history_renewed_at", "renewal_history", ["renewed_at"])
    op.create_table(
        "ai_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interaction_id", sa.Integer(), sa.ForeignKey("ai_interactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("helpful", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_feedback_interaction_id", "ai_feedback", ["interaction_id"])
    op.create_index("ix_ai_feedback_user_id", "ai_feedback", ["user_id"])
    op.create_index("uq_ai_feedback_user_interaction", "ai_feedback", ["interaction_id", "user_id"], unique=True)


def downgrade() -> None:
    op.drop_table("ai_feedback")
    op.drop_table("renewal_history")
    op.drop_column("borrowings", "renewal_count")
