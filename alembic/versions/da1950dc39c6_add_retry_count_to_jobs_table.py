"""Add retry_count to jobs table

Revision ID: da1950dc39c6
Revises: 8d0f3e88d06e
Create Date: 2025-07-26 20:18:58.327856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da1950dc39c6'
down_revision: Union[str, Sequence[str], None] = '8d0f3e88d06e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
