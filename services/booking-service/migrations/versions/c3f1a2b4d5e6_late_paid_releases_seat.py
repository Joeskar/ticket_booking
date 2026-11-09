"""late_paid releases seat

Revision ID: c3f1a2b4d5e6
Revises: a99a88b7b9e6
Create Date: 2026-11-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3f1a2b4d5e6"
down_revision: Union[str, Sequence[str], None] = "a99a88b7b9e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("uq_bookings_active_seat", table_name="bookings")
    op.create_index(
        "uq_bookings_active_seat",
        "bookings",
        ["screening_id", "seat_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('EXPIRED', 'LATE_PAID')"),
    )


def downgrade() -> None:
    op.drop_index("uq_bookings_active_seat", table_name="bookings")
    op.create_index(
        "uq_bookings_active_seat",
        "bookings",
        ["screening_id", "seat_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'EXPIRED'"),
    )
