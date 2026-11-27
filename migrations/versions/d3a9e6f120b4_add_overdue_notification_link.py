"""Link overdue reminders to loans and prevent duplicate reminders."""
from alembic import op
import sqlalchemy as sa

revision = 'd3a9e6f120b4'
down_revision = 'c2d9e4a7b615'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notifications') as batch:
        batch.add_column(sa.Column('borrowing_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_notification_borrowing', 'borrowings', ['borrowing_id'], ['id'], ondelete='SET NULL')
    op.create_index('uq_overdue_notice_per_loan', 'notifications', ['borrowing_id'], unique=True,
                    sqlite_where=sa.text("type = 'OVERDUE_REMINDER'"), postgresql_where=sa.text("type = 'OVERDUE_REMINDER'"))


def downgrade():
    op.drop_index('uq_overdue_notice_per_loan', table_name='notifications')
    with op.batch_alter_table('notifications') as batch:
        batch.drop_constraint('fk_notification_borrowing', type_='foreignkey')
        batch.drop_column('borrowing_id')
