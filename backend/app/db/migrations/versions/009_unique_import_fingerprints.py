"""enforce uniqueness for imported record fingerprints

Revision ID: 009_unique_import_fingerprints
Revises: 008_protect_import_confirmation
Create Date: 2026-08-13
"""

from alembic import op


revision = "009_unique_import_fingerprints"
down_revision = "008_protect_import_confirmation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This revision is intentionally a compatibility no-op. Semantic
    # fingerprints are not identities: repeated rows from different source
    # contexts must survive until revision 010 installs source-row identity.
    # Keeping the revision preserves the upgrade chain for databases that have
    # already recorded 008 without destructively rewriting their data.
    pass


def downgrade() -> None:
    pass
