import uuid

from sqlalchemy.orm import Session

from claim360.audit import append_audit
from claim360.models.enums import Actor, AuditEventType


class FixturePaymentAdapter:
    def record_disposition(self, db: Session, claim_id: uuid.UUID, decision: str) -> dict:
        append_audit(
            db,
            claim_id,
            AuditEventType.DISPOSITION_STUBBED,
            Actor.SYSTEM,
            {"decision": decision, "paid": False},
        )
        return {"recorded": True, "paid": False, "claim_id": str(claim_id)}
