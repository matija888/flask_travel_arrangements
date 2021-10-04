"""add user_id column in reservation table

Revision ID: 7b8e2ca5fb9b
Revises: 1a0dc86e912e
Create Date: 2021-10-04 23:00:10.521697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b8e2ca5fb9b'
down_revision = '1a0dc86e912e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservation', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_reservation_user_id', 'reservation', 'user', ['user_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_reservation_user_id', 'reservation', type_='foreignkey')
    op.drop_column('reservation', 'user_id')
