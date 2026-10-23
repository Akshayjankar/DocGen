"""Drop unused ApiKey table (Revision 2 WP0).

Revision ID: 20261023_0001
Revises:
Create Date: 2026-10-23
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261023_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    # SQLModel default table name for class ApiKey
    for name in ("apikey", "api_key", "ApiKey"):
        if name in tables:
            op.drop_table(name)


def downgrade() -> None:
    # ApiKey is intentionally not restored — product no longer uses API keys.
    pass
