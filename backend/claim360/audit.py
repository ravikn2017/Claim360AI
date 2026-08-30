import uuid
from typing import Any

from sqlalchemy.orm import Session

from claim360.models.enums import Actor, AuditEventType
from claim360.models.orm import AuditEvent


def append_audit(
    db: Session,
    claim_id: uuid.UUID,
    event_type: AuditEventType | str,
    actor: Actor | str,
    payload: dict[str, Any],
) -> AuditEvent:
    """Insert-only audit write. Callers must not update or delete audit rows."""
    event = AuditEvent(
        claim_id=claim_id,
        event_type=str(event_type),
        actor=str(actor),
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event
