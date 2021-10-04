"""add travel_guide_id column in arrangement table

Revision ID: 0c8df583c631
Revises: a009f9a4a688
Create Date: 2021-10-04 13:27:45.850001

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c8df583c631'
down_revision = 'a009f9a4a688'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('arrangement', sa.Column('travel_guide_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_travel_guide', 'arrangement', 'user', ['travel_guide_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_travel_guide', 'arrangement', type_='foreignkey')
    op.drop_column('arrangement', 'travel_guide_id')
