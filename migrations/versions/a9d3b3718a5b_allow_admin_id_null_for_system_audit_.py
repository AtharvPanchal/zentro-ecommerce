from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a9d3b3718a5b"
down_revision = "c86118f6d133"   # ✅ LAST VALID MIGRATION
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "admin_activity_logs",
        "admin_id",
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade():
    op.alter_column(
        "admin_activity_logs",
        "admin_id",
        existing_type=sa.Integer(),
        nullable=False
    )
