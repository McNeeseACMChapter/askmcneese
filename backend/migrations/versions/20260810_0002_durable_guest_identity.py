"""Persist anonymous guest identity, allowance, and feedback in PostgreSQL."""

from alembic import op
import sqlalchemy as sa

revision = "20260810_0002"
down_revision = "20260809_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guest_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("public_guest_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("last_seen_at", sa.String(length=64), nullable=False),
        sa.Column("tour_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tour_current_step", sa.String(length=64), nullable=True),
        sa.Column("tour_started_at", sa.String(length=64), nullable=True),
        sa.Column("tour_completed_at", sa.String(length=64), nullable=True),
        sa.Column("questions_used", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("public_guest_id", name="uq_guest_sessions_public_guest_id"),
        sa.UniqueConstraint("token_hash", name="uq_guest_sessions_token_hash"),
    )
    op.create_index("idx_guest_token", "guest_sessions", ["token_hash"], unique=False)

    op.create_table(
        "guest_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "guest_session_id",
            sa.Integer(),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("page_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "idx_guest_feedback_created",
        "guest_feedback",
        [sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_guest_feedback_created", table_name="guest_feedback")
    op.drop_table("guest_feedback")
    op.drop_index("idx_guest_token", table_name="guest_sessions")
    op.drop_table("guest_sessions")
