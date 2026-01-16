"""enhance admin activity logs

Revision ID: c86118f6d133
Revises: 83136b17de67
Create Date: 2026-01-02 22:34:57.601643
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c86118f6d133'
down_revision = '83136b17de67'
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================
    # ADMIN ACTIVITY LOGS
    # ONLY alter action column length
    # =====================================================
    with op.batch_alter_table('admin_activity_logs', schema=None) as batch_op:
        batch_op.alter_column(
            'action',
            existing_type=mysql.VARCHAR(
                length=100,
                collation='utf8mb4_unicode_ci'
            ),
            type_=sa.String(length=255),
            existing_nullable=False
        )


def downgrade():
    # =====================================================
    # REVERT action column length
    # =====================================================
    with op.batch_alter_table('admin_activity_logs', schema=None) as batch_op:
        batch_op.alter_column(
            'action',
            existing_type=sa.String(length=255),
            type_=mysql.VARCHAR(
                length=100,
                collation='utf8mb4_unicode_ci'
            ),
            existing_nullable=False
        )
