import uuid

from sqlalchemy import select

from claim360.audit import append_audit
from claim360.config import Settings
from claim360.models.enums import Actor, AuditEventType, ClaimStatus
from claim360.models.orm import AuditEvent, Claim, User
from claim360.models.schemas import ClaimPayload
from claim360.seed import seed_specialist_user
from tests.conftest import SAMPLE_CLAIM, requires_postgres


@requires_postgres
def test_insert_claim_and_audit_event(db) -> None:
    payload = ClaimPayload.model_validate(SAMPLE_CLAIM)
    claim = Claim(
        portal_claim_ref=f"CLM-{uuid.uuid4().hex[:8]}",
        status=ClaimStatus.RECEIVED.value,
        payload=payload.model_dump(mode="json"),
        member_external_id=payload.member_external_id,
        agent_versions={},
    )
    db.add(claim)
    db.flush()

    event = append_audit(
        db,
        claim.id,
        AuditEventType.CLAIM_RECEIVED,
        Actor.PORTAL,
        {"portal_claim_ref": claim.portal_claim_ref},
    )

    stored_claim = db.get(Claim, claim.id)
    stored_event = db.scalar(select(AuditEvent).where(AuditEvent.id == event.id))
    assert stored_claim is not None
    assert stored_claim.status == ClaimStatus.RECEIVED
    assert stored_event is not None
    assert stored_event.event_type == AuditEventType.CLAIM_RECEIVED
    assert stored_event.actor == Actor.PORTAL


@requires_postgres
def test_seed_specialist_user(db) -> None:
    settings = Settings(
        specialist_email=f"specialist-{uuid.uuid4().hex[:8]}@local",
        specialist_password="test-pass-l1",
    )
    user = seed_specialist_user(db, settings)
    assert user is not None
    again = seed_specialist_user(db, settings)
    assert again is not None and again.id == user.id
    assert db.scalar(select(User).where(User.email == settings.specialist_email)) is not None
