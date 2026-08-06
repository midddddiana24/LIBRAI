"""add user profile photo

Revision ID: ac82f18f4be1
Revises: 7193d547b085
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "ac82f18f4be1"
down_revision: Union[str, Sequence[str], None] = "7193d547b085"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("photo_image", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "photo_image")
