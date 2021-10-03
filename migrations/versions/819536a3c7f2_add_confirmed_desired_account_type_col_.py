"""add confirmed_desired_account_type col in user table

Revision ID: 819536a3c7f2
Revises: 2545ed06d920
Create Date: 2021-10-03 17:06:34.307257

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '819536a3c7f2'
down_revision = '2545ed06d920'
branch_labels = None
depends_on = None


def upgrade():
    confirmed_desired_account_type = postgresql.ENUM(
        'approve', 'reject', 'pending', name='confirmed_desired_account_type'
    )
    confirmed_desired_account_type.create(op.get_bind())
    op.add_column(
        'user',
        sa.Column(
            'confirmed_desired_account_type',
            sa.Enum('approve', 'reject', 'pending', name='confirmed_desired_account_type'),
            nullable=True
        )
    )
    op.alter_column(
        'user', 'desired_account_type',
        existing_type=postgresql.ENUM('TOURIST', 'TRAVEL GUIDE', 'ADMIN', name='desired_account_type'),
        nullable=False
    )


def downgrade():
    op.alter_column(
        'user', 'desired_account_type',
        existing_type=postgresql.ENUM('TOURIST', 'TRAVEL GUIDE', 'ADMIN', name='desired_account_type'),
        nullable=True
    )
    op.drop_column('user', 'confirmed_desired_account_type')
