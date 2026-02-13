"""fix_pp_status_rascunho_to_aprovado

Revision ID: 93ca473ea37e
Revises: k7l8m9n0p1q2
Create Date: 2026-02-08 23:40:57.686160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93ca473ea37e'
down_revision: Union[str, None] = 'k7l8m9n0p1q2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Mudar status de 'rascunho' para 'aprovado' em todas as Pesquisas de Preços
    op.execute("""
        UPDATE pesquisas_precos
        SET status = 'aprovado'
        WHERE status = 'rascunho'
    """)


def downgrade() -> None:
    # Reverter: aprovado → rascunho (se necessário)
    op.execute("""
        UPDATE pesquisas_precos
        SET status = 'rascunho'
        WHERE status = 'aprovado'
    """)
