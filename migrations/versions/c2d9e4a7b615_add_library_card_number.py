"""Keep campus and library card numbers separate."""
from alembic import op
import sqlalchemy as sa

revision = "c2d9e4a7b615"
down_revision = "f1a8c9d3e721"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("library_card_number", sa.String(80), nullable=True))
    op.create_index("ix_users_library_card_number", "users", ["library_card_number"], unique=True)


def downgrade():
    op.drop_index("ix_users_library_card_number", table_name="users")
    op.drop_column("users", "library_card_number")
