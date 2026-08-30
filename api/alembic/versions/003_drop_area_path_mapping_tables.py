"""drop area path mapping tables

The area-path-mapping-config screen (per-path overrides + a configurable
splitting rule, both persisted) was replaced by a stateless parser
(services/areapath_parser.py) driven entirely by the DM's WIQL query — no
config screen, no per-path state needed. ado_connections.wiql_query already
existed from migration 002 and needs no change.

Revision ID: 003
Revises: 002
Create Date: 2026-08-31

"""
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())

    for table in ("area_path_mappings", "area_path_mapping_rules"):
        if table in existing:
            op.drop_table(table)


def downgrade() -> None:
    # Intentionally not recreated — the tables' schema is fully described in
    # migration 002 if this ever needs to be reverted by hand.
    pass
