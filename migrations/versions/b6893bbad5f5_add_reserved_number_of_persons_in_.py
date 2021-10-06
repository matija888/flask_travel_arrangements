"""add reserved_number_of_persons in arrangement table

Revision ID: b6893bbad5f5
Revises: 7b8e2ca5fb9b
Create Date: 2021-10-06 22:11:03.292226

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6893bbad5f5'
down_revision = '7b8e2ca5fb9b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('arrangement', sa.Column('reserved_number_of_persons', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('arrangement', 'reserved_number_of_persons')