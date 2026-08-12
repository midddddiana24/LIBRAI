"""add fines and email deliveries

Revision ID: e9c1b7a4d2f0
Revises: bb921a0cd347
Create Date: 2026-08-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9c1b7a4d2f0"
down_revision: Union[str, None] = "bb921a0cd347"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("borrowing_id", sa.Integer(), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["borrowing_id"], ["borrowings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fines_assessed_at"), "fines", ["assessed_at"], unique=False)
    op.create_index(op.f("ix_fines_borrowing_id"), "fines", ["borrowing_id"], unique=False)
    op.create_index(op.f("ix_fines_status"), "fines", ["status"], unique=False)
    op.create_index(op.f("ix_fines_user_id"), "fines", ["user_id"], unique=False)

    op.create_table(
        "email_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("notification_id", sa.Integer(), nullable=True),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_deliveries_created_at"), "email_deliveries", ["created_at"], unique=False)
    op.create_index(op.f("ix_email_deliveries_notification_id"), "email_deliveries", ["notification_id"], unique=False)
    op.create_index(op.f("ix_email_deliveries_recipient"), "email_deliveries", ["recipient"], unique=False)
    op.create_index(op.f("ix_email_deliveries_status"), "email_deliveries", ["status"], unique=False)
    op.create_index(op.f("ix_email_deliveries_user_id"), "email_deliveries", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_deliveries_user_id"), table_name="email_deliveries")
    op.drop_index(op.f("ix_email_deliveries_status"), table_name="email_deliveries")
    op.drop_index(op.f("ix_email_deliveries_recipient"), table_name="email_deliveries")
    op.drop_index(op.f("ix_email_deliveries_notification_id"), table_name="email_deliveries")
    op.drop_index(op.f("ix_email_deliveries_created_at"), table_name="email_deliveries")
    op.drop_table("email_deliveries")
    op.drop_index(op.f("ix_fines_user_id"), table_name="fines")
    op.drop_index(op.f("ix_fines_status"), table_name="fines")
    op.drop_index(op.f("ix_fines_borrowing_id"), table_name="fines")
    op.drop_index(op.f("ix_fines_assessed_at"), table_name="fines")
    op.drop_table("fines")
