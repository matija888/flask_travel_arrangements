"""add price column in reservation table

Revision ID: 1a0dc86e912e
Revises: 31ad3966b607
Create Date: 2021-10-04 22:37:03.765784

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a0dc86e912e'
down_revision = '31ad3966b607'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservation', sa.Column('price', sa.Numeric(precision=9, scale=2), nullable=False))


def downgrade():
    op.drop_column('reservation', 'price')
