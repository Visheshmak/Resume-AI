"""Store structured job description extraction.

Revision ID: 0002_job_structured_data
Revises: 0001_initial_schema
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_job_structured_data"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("job_descriptions")}
    if "structured_data" not in columns:
        op.add_column("job_descriptions", sa.Column("structured_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("job_descriptions")}
    if "structured_data" in columns:
        op.drop_column("job_descriptions", "structured_data")
