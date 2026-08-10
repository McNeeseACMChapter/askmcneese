"""Class Planner PostgreSQL-ready normalized data platform."""
from alembic import op
from app.services.class_planner.db import metadata
revision = "20260809_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    metadata.create_all(bind=bind, checkfirst=True)
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_courses_title_trgm "
            "ON courses USING gin (normalized_title gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_courses_code_trgm "
            "ON courses USING gin (normalized_code gin_trgm_ops)"
        )

def downgrade() -> None:
    metadata.drop_all(bind=op.get_bind(), checkfirst=True)
