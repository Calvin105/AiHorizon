"""cases.escalation_note — what the operator was stuck on

`escalate` has been on the case since the initial schema, but nothing set
it and nothing showed it. It now backs the wizard's "Ask an engineer"
button and the home page's Needs review tile. The flag alone tells a
reviewer *that* someone is stuck, not *on what*, and reconstructing the
question from the transcript is the slow part of a review — so the
operator's one line is kept next to it.

Existing rows backfill NULL: no case was ever escalated.

Revision ID: e4c9a2d76b10
Revises: d3b8c0a51f47
Create Date: 2026-10-01

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4c9a2d76b10'
down_revision: Union[str, Sequence[str], None] = 'd3b8c0a51f47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('cases', sa.Column('escalation_note', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cases', 'escalation_note')
