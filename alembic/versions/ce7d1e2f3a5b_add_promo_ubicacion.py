"""agregar ubicacion (direccion, lat/lng) de canje a promotions y redemption_tickets

Revision ID: ce7d1e2f3a5b
Revises: b5c9d1e2f3a4
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce7d1e2f3a5b'
down_revision: Union[str, Sequence[str], None] = 'b5c9d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('promotions', sa.Column('direccion', sa.String(), nullable=True))
    op.add_column('promotions', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('promotions', sa.Column('longitude', sa.Float(), nullable=True))

    op.add_column('redemption_tickets', sa.Column('direccion', sa.String(), nullable=True))
    op.add_column('redemption_tickets', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('redemption_tickets', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('redemption_tickets', 'longitude')
    op.drop_column('redemption_tickets', 'latitude')
    op.drop_column('redemption_tickets', 'direccion')

    op.drop_column('promotions', 'longitude')
    op.drop_column('promotions', 'latitude')
    op.drop_column('promotions', 'direccion')