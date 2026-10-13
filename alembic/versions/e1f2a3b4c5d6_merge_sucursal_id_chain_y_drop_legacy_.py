"""merge sucursal_id chain y drop legacy support reply

Revision ID: e1f2a3b4c5d6
Revises: c3d4e5f6a7b8, f9a8b7c6d5e4
Create Date: 2026-10-12 13:44:33.706195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = ('c3d4e5f6a7b8', 'f9a8b7c6d5e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
