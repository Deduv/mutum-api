"""merge heads

Revision ID: 765cbcbcb6b1
Revises: b3f8a2c91d47, f5935b2973e6
Create Date: 2026-06-25 21:15:36.969972

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '765cbcbcb6b1'
down_revision: Union[str, Sequence[str], None] = ('b3f8a2c91d47', 'f5935b2973e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
