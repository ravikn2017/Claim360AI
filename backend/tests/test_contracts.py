from datetime import date

import pytest
from pydantic import ValidationError

from claim360.models.schemas import (
    ClaimPayload,
    FraudOutput,
    LetterDraft,
    MedNecOutput,
    PolicyOutput,
)
from tests.conftest import SAMPLE_CLAIM


def test_claim_payload_accepts_lld_example() -> None:
    payload = ClaimPayload.model_validate(SAMPLE_CLAIM)
    assert payload.member_external_id == "MEM-001"
    assert payload.date_of_service == date(2026, 6, 1)


def test_claim_payload_rejects_missing_fields() -> None:
    with pytest.raises(ValidationError):
        ClaimPayload.model_validate({"portal_claim_ref": "CLM-1001"})


def test_agent_outputs_and_letter_validate() -> None:
    PolicyOutput.model_validate(
        {
            "outcome": "eligible",
            "field_findings": [
                {"field": "procedure_codes", "status": "pass", "message": "covered"}
            ],
            "policy_refs": ["POL-PT-001"],
            "confidence": 0.9,
        }
    )
    FraudOutput.model_validate(
        {
            "risk_level": "low",
            "risk_score": 10,
            "indicators": [],
            "confidence": 0.8,
        }
    )
    MedNecOutput.model_validate(
        {
            "determination": "necessary",
            "guideline_refs": ["GL-LBP-01"],
            "rationale": "Meets visit criteria.",
            "confidence": 0.85,
        }
    )
    letter = LetterDraft.model_validate({"subject": "Claim update", "body": "Approved pending review."})
    assert letter.subject
