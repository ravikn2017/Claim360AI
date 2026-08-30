from datetime import date
from uuid import uuid4

from claim360.adapters import (
    FixtureCommsAdapter,
    FixtureEligibilityAdapter,
    FixtureGuidelineAdapter,
    FixtureHistoryAdapter,
    FixturePolicySnippetAdapter,
)
from tests.conftest import SAMPLE_CLAIM


def test_eligibility_history_guidelines_for_mem_001() -> None:
    dos = date.fromisoformat(SAMPLE_CLAIM["date_of_service"])
    eligibility = FixtureEligibilityAdapter().get_eligibility("MEM-001", dos)
    history = FixtureHistoryAdapter().get_claims("MEM-001")
    guidelines = FixtureGuidelineAdapter().match(
        SAMPLE_CLAIM["diagnosis_codes"],
        SAMPLE_CLAIM["procedure_codes"],
    )

    assert eligibility.found is True
    assert eligibility.status == "active"
    assert eligibility.active_on_dos is True
    assert "97110" in eligibility.covered_procedures
    assert "POL-PT-001" in eligibility.policy_refs

    assert history.found is True
    assert history.claims[0].portal_claim_ref == "CLM-0901"

    assert [hit.guideline_id for hit in guidelines.hits] == ["GL-LBP-01"]
    assert guidelines.hits[0].determination_hint == "necessary"


def test_unknown_member_does_not_crash() -> None:
    eligibility = FixtureEligibilityAdapter().get_eligibility("MEM-UNKNOWN", date(2026, 6, 1))
    history = FixtureHistoryAdapter().get_claims("MEM-UNKNOWN")

    assert eligibility.found is False
    assert eligibility.status == "unknown"
    assert eligibility.active_on_dos is False
    assert history.found is False
    assert history.claims == []


def test_policy_snippets_and_comms_stub() -> None:
    snippets = FixturePolicySnippetAdapter().snippets(["POL-PT-001", "MISSING"])
    assert len(snippets) == 1
    assert snippets[0].ref == "POL-PT-001"

    queued = FixtureCommsAdapter().queue_member_letter(uuid4(), "Subject", "Body")
    assert queued["queued"] is True
    assert queued["sent"] is False
