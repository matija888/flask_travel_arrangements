"""create user table

Revision ID: b2974053473b
Revises: 
Create Date: 2021-09-30 17:24:51.076547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2974053473b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('first_name', sa.String(length=100), nullable=False),
                    sa.Column('last_name', sa.String(length=100), nullable=False),
                    sa.Column('email', sa.String(length=100), nullable=False),
                    sa.Column('username', sa.String(length=100), nullable=False),
                    sa.Column('password', sa.String(length=100), nullable=False),
                    sa.Column('confirmed_password', sa.String(length=100), nullable=False),
                    sa.Column('account_type', sa.Enum('ADMIN', 'TRAVEL GUIDE', 'TOURIST', name='account_type'), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('user')
