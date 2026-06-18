"""add user status

Revision ID: 5344c2d59f82
Revises: 7fcc27cbc989
Create Date: 2026-06-08 16:30:38.370910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5344c2d59f82'
down_revision: Union[str, Sequence[str], None] = '7fcc27cbc989'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    user_status_enum = sa.Enum("PENDING", "ACTIVE", name="userstatus")
    user_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "status",
            user_status_enum,
            server_default="ACTIVE",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "status")

    user_status_enum = sa.Enum("PENDING", "ACTIVE", name="userstatus")
    user_status_enum.drop(op.get_bind(), checkfirst=True)
