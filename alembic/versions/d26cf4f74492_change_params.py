"""change params

Revision ID: d26cf4f74492
Revises: a1373c571bd3
Create Date: 2024-09-20 16:41:23.093902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd26cf4f74492'
down_revision: Union[str, None] = 'a1373c571bd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('multiplier_params', 'critical_hit_chance')
    op.drop_column('multiplier_params', 'spirit')
    op.drop_column('multiplier_params', 'true_damage')
    op.drop_column('summand_params', 'critical_hit_chance')
    op.drop_column('summand_params', 'spirit')
    op.drop_column('summand_params', 'true_damage')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('summand_params', sa.Column('true_damage', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('summand_params', sa.Column('spirit', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('summand_params', sa.Column('critical_hit_chance', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('multiplier_params', sa.Column('true_damage', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('multiplier_params', sa.Column('spirit', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('multiplier_params', sa.Column('critical_hit_chance', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    # ### end Alembic commands ###