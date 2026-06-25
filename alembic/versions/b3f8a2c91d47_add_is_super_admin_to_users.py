"""add is_super_admin to users

Revision ID: b3f8a2c91d47
Revises: dd693df4ca35
Create Date: 2026-06-25 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f8a2c91d47'
down_revision: Union[str, Sequence[str], None] = 'dd693df4ca35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_super_admin boolean column to users table."""
    op.add_column(
        'users',
        sa.Column(
            'is_super_admin',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )


def downgrade() -> None:
    """Remove is_super_admin column from users table."""
    op.drop_column('users', 'is_super_admin')
