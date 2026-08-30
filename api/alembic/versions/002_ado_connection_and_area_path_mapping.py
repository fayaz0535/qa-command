"""ado connection and area path mapping

Revision ID: 002
Revises: 001
Create Date: 2026-08-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _create_table_if_missing(inspector, name, *columns_and_constraints):
    if name not in inspector.get_table_names():
        op.create_table(name, *columns_and_constraints)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _create_table_if_missing(
        inspector, "ado_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_url", sa.String(500), nullable=False),
        sa.Column("project", sa.String(255), nullable=False),
        sa.Column("encrypted_pat", sa.Text(), nullable=False),
        sa.Column("wiql_query", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("last_sync_summary", postgresql.JSON(), nullable=True),
    )

    _create_table_if_missing(
        inspector, "area_path_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("area_path", sa.String(1000), nullable=False),
        sa.Column("platform", sa.String(255), nullable=True),
        sa.Column("module", sa.String(255), nullable=True),
        sa.Column("sub_module", sa.String(255), nullable=True),
        sa.Column("is_override", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("area_path", name="uq_area_path"),
    )

    _create_table_if_missing(
        inspector, "area_path_mapping_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("drop_root_segments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("platform_segments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("module_segments", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())

    for table in ("area_path_mapping_rules", "area_path_mappings", "ado_connections"):
        if table in existing:
            op.drop_table(table)
