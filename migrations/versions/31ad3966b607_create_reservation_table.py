"""create reservation table

Revision ID: 31ad3966b607
Revises: 0c8df583c631
Create Date: 2021-10-04 22:08:43.133603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31ad3966b607'
down_revision = '0c8df583c631'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reservation',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('arrangement_id', sa.Integer(), nullable=False),
                    sa.Column('number_of_persons', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['arrangement_id'], ['arrangement.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('reservation')
