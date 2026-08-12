"""add operational query indexes"""
from typing import Sequence, Union
from alembic import op

revision: str = "f1a8c9d3e721"
down_revision: Union[str, None] = "e9c1b7a4d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_index("ix_borrowing_user_status_due", "borrowings", ["user_id", "status", "due_at"])
    op.create_index("ix_audit_actor_date", "audit_logs", ["actor_type", "actor_id", "created_at"])
    op.create_index("ix_email_status_created", "email_deliveries", ["status", "created_at"])
    op.create_index("ix_search_zero_results", "search_history", ["results_count", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_search_zero_results", table_name="search_history")
    op.drop_index("ix_email_status_created", table_name="email_deliveries")
    op.drop_index("ix_audit_actor_date", table_name="audit_logs")
    op.drop_index("ix_borrowing_user_status_due", table_name="borrowings")
