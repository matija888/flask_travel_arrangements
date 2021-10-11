"""add created_by column in arrangement table

Revision ID: a035c9862a20
Revises: b6893bbad5f5
Create Date: 2021-10-11 23:14:57.301903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a035c9862a20'
down_revision = 'b6893bbad5f5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('arrangement', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_created_by', 'arrangement', 'user', ['created_by'], ['id'])


def downgrade():
    op.drop_constraint('fk_created_by', 'arrangement', type_='foreignkey')
    op.drop_column('arrangement', 'created_by')
