"""add tools column to skills

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-02-07 07:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tools column using raw SQL for JSON type compatibility/simplicity
    # Using sqlalchemy's JSON type abstraction
    op.add_column('skills', sa.Column('tools', sa.JSON(), nullable=True, comment='Lista de ferramentas habilitadas pela skill'))


def downgrade() -> None:
    op.drop_column('skills', 'tools')
