from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '551626283b4f'
down_revision = '16aad854975e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_categories_parent_id', ['parent_id'], unique=False)
        batch_op.create_foreign_key(None, 'categories', ['parent_id'], ['id'])


def downgrade():
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index('ix_categories_parent_id')
        batch_op.drop_column('parent_id')