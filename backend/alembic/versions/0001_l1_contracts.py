"""L1 claims, findings, audit, users

Revision ID: 0001_l1
Revises:
Create Date: 2026-08-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_l1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="specialist"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("portal_claim_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("member_external_id", sa.Text(), nullable=False),
        sa.Column("proposed_decision", sa.Text(), nullable=True),
        sa.Column("proposed_rationale", postgresql.JSONB(), nullable=True),
        sa.Column("final_decision", sa.Text(), nullable=True),
        sa.Column("final_rationale", postgresql.JSONB(), nullable=True),
        sa.Column("draft_letter", sa.Text(), nullable=True),
        sa.Column("final_letter", sa.Text(), nullable=True),
        sa.Column("agent_versions", postgresql.JSONB(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("portal_claim_ref"),
    )
    op.create_index("ix_claims_status", "claims", ["status"])
    op.create_index("ix_claims_portal_claim_ref", "claims", ["portal_claim_ref"])
    op.create_table(
        "agent_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("agent", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_findings_claim_id", "agent_findings", ["claim_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_claim_id_created_at", "audit_events", ["claim_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_claim_id_created_at", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_agent_findings_claim_id", table_name="agent_findings")
    op.drop_table("agent_findings")
    op.drop_index("ix_claims_portal_claim_ref", table_name="claims")
    op.drop_index("ix_claims_status", table_name="claims")
    op.drop_table("claims")
    op.drop_table("users")
