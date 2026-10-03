"""rule_overrides — engineer edits to rule weights

The rules page lists every rule with the weight the NPL guide or the NSW
brief supports. An engineer can change one, with a reason; the change is
a row here, applied by ranking/weights.py, and deleting the row restores
the manual's weight. An empty table is the rules exactly as written.

Revision ID: f7a2c4e9d318
Revises: e4c9a2d76b10
Create Date: 2026-10-03

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f7a2c4e9d318'
down_revision: Union[str, Sequence[str], None] = 'e4c9a2d76b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'rule_overrides',
        sa.Column('rule_key', sa.String(length=160), primary_key=True),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('rule_overrides')
