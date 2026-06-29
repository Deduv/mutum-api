"""Add is_email_verified to User

Revision ID: 8532507e234b
Revises: 063c551526f6
Create Date: 2026-06-28 21:36:07.615592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8532507e234b'
down_revision: Union[str, Sequence[str], None] = '063c551526f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), server_default='false', nullable=False))
    op.execute("UPDATE users SET is_email_verified = true")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_email_verified')
