"""Add artifacts table for persistent growth artifacts

Revision ID: 003_artifacts
Revises: 002_documents_and_chunks
Create Date: 2026-09-13 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_artifacts"
down_revision: Union[str, None] = "002_documents_and_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("content_format", sa.String(length=20), server_default="markdown", nullable=False),
        sa.Column("schema_version", sa.String(length=20), server_default="v1.0", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "idx_artifacts_session_id",
        "artifacts",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "idx_artifacts_message_id",
        "artifacts",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        "idx_artifacts_artifact_type",
        "artifacts",
        ["artifact_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_artifacts_artifact_type", table_name="artifacts")
    op.drop_index("idx_artifacts_message_id", table_name="artifacts")
    op.drop_index("idx_artifacts_session_id", table_name="artifacts")
    op.drop_table("artifacts")
