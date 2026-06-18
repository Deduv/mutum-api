"""normalize user emails

Revision ID: 2be99416133e
Revises: dd693df4ca35
Create Date: 2026-06-18 18:20:06.855176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2be99416133e'
down_revision: Union[str, Sequence[str], None] = 'dd693df4ca35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    # Check for duplicates before updating
    result = connection.execute(sa.text("""
        SELECT lower(trim(email)), COUNT(*) 
        FROM users 
        GROUP BY lower(trim(email)) 
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    
    if duplicates:
        raise ValueError(f"Cannot normalize emails: found duplicates case-insensitive: {duplicates}")

    # Proceed with normalization
    op.execute("UPDATE users SET email = lower(trim(email))")


def downgrade() -> None:
    """Downgrade schema."""
    pass
