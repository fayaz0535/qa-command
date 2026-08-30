"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def _create_table_if_missing(inspector, name, *columns_and_constraints):
    """Safety net alongside removing the app's own create_all() call — lets
    `alembic upgrade head` run cleanly even if a table already exists (e.g. a
    stale DB from before that call was removed) instead of erroring out."""
    if name not in inspector.get_table_names():
        op.create_table(name, *columns_and_constraints)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    defect_source_enum = postgresql.ENUM("CSV", "ADO", "JIRA", name="defectsource")
    defect_source_enum.create(bind, checkfirst=True)

    defect_severity_enum = postgresql.ENUM("Critical", "High", "Medium", "Low", "TBC", name="defectseverity")
    defect_severity_enum.create(bind, checkfirst=True)

    test_status_enum = postgresql.ENUM("Passed", "Failed", "Blocked", "Not Run", "In Progress", name="teststatus")
    test_status_enum.create(bind, checkfirst=True)

    test_phase_enum = postgresql.ENUM("SIT", "UAT", "BVT", "Parallel Run", name="testphase")
    test_phase_enum.create(bind, checkfirst=True)

    hierarchy_level_enum = postgresql.ENUM("overall", "platform", "module", "sub_module", name="hierarchylevel")
    hierarchy_level_enum.create(bind, checkfirst=True)

    _create_table_if_missing(
        inspector, "platforms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.UniqueConstraint("name", name="uq_platform_name"),
    )

    _create_table_if_missing(
        inspector, "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.UniqueConstraint("platform_id", "name", name="uq_module_platform_name"),
    )

    _create_table_if_missing(
        inspector, "sub_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modules.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.UniqueConstraint("module_id", "name", name="uq_submodule_module_name"),
    )

    _create_table_if_missing(
        inspector, "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.UniqueConstraint("domain", name="uq_vendor_domain"),
    )

    _create_table_if_missing(
        inspector, "defects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("source", postgresql.ENUM("CSV", "ADO", "JIRA", name="defectsource", create_type=False),
                   nullable=False),
        sa.Column("platform", sa.String(255), nullable=True),
        sa.Column("module", sa.String(255), nullable=True),
        sa.Column("sub_module", sa.String(255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("severity", postgresql.ENUM("Critical", "High", "Medium", "Low", "TBC",
                   name="defectseverity", create_type=False), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("owner_vendor", sa.String(255), nullable=True),
        sa.Column("vendor_needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("assignee_email", sa.String(255), nullable=True),
        sa.Column("raised_date", sa.Date(), nullable=True),
        sa.Column("eta", sa.Date(), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_reopen", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("source", "external_id", name="uq_defect_source_external_id"),
    )

    _create_table_if_missing(
        inspector, "test_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("source", postgresql.ENUM("CSV", "ADO", "JIRA", name="defectsource", create_type=False),
                   nullable=False),
        sa.Column("platform", sa.String(255), nullable=True),
        sa.Column("module", sa.String(255), nullable=True),
        sa.Column("sub_module", sa.String(255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", postgresql.ENUM("Passed", "Failed", "Blocked", "Not Run", "In Progress",
                   name="teststatus", create_type=False), nullable=False),
        sa.Column("phase", postgresql.ENUM("SIT", "UAT", "BVT", "Parallel Run",
                   name="testphase", create_type=False), nullable=True),
        sa.Column("executed_date", sa.Date(), nullable=True),
        sa.UniqueConstraint("source", "external_id", name="uq_testcase_source_external_id"),
    )

    _create_table_if_missing(
        inspector, "metric_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("level", postgresql.ENUM("overall", "platform", "module", "sub_module",
                   name="hierarchylevel", create_type=False), nullable=False),
        sa.Column("platform", sa.String(255), nullable=True),
        sa.Column("module", sa.String(255), nullable=True),
        sa.Column("sub_module", sa.String(255), nullable=True),
        sa.Column("execution_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pass_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("open_defects", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_critical", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_high", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_medium", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_low", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("closed_defects", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aging_gt7", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aging_gt14", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aging_gt21", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_resolution_days", sa.Float(), nullable=True),
        sa.Column("health", sa.String(10), nullable=False, server_default="green"),
        sa.UniqueConstraint("snapshot_date", "level", "platform", "module", "sub_module",
                             name="uq_snapshot_date_node"),
    )

    _create_table_if_missing(
        inspector, "send_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default="Daily QA Report"),
        sa.Column("recipients", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("cc", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("send_time", sa.String(5), nullable=False, server_default="08:00"),
        sa.Column("auto_send_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())

    for table in ("send_configs", "metric_snapshots", "test_cases", "defects",
                  "vendors", "sub_modules", "modules", "platforms"):
        if table in existing:
            op.drop_table(table)

    postgresql.ENUM(name="hierarchylevel").drop(bind, checkfirst=True)
    postgresql.ENUM(name="testphase").drop(bind, checkfirst=True)
    postgresql.ENUM(name="teststatus").drop(bind, checkfirst=True)
    postgresql.ENUM(name="defectseverity").drop(bind, checkfirst=True)
    postgresql.ENUM(name="defectsource").drop(bind, checkfirst=True)
