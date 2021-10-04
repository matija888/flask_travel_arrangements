"""create arrangement table

Revision ID: b9df6d2c337d
Revises: 819536a3c7f2
Create Date: 2021-10-03 20:08:25.403699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9df6d2c337d'
down_revision = '819536a3c7f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('arrangement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('destination', sa.String(length=50), nullable=False),
    sa.Column('number_of_persons', sa.Integer(), nullable=False),
    sa.Column('price', sa.Numeric(precision=9, scale=2), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('arrangement')
    # ### end Alembic commands ###