"""Create the initial ResumeIQ relational schema.

Revision ID: 0001_initial_schema
Revises:
"""

from alembic import op

import app.models.entities  # noqa: F401
from app.models import Base

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
