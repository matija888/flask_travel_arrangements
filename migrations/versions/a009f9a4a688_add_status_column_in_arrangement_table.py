"""add status column in arrangement table

Revision ID: a009f9a4a688
Revises: b9df6d2c337d
Create Date: 2021-10-04 12:39:47.396919

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a009f9a4a688'
down_revision = 'b9df6d2c337d'
branch_labels = None
depends_on = None


def upgrade():
    status = postgresql.ENUM('active', 'inactive', name='status')
    status.create(op.get_bind())
    op.add_column('arrangement', sa.Column('status', sa.Enum('active', 'inactive', name='status'), nullable=True))


def downgrade():
    op.drop_column('arrangement', 'status')
