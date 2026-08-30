"""Tests for ValidationAgent."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from claim360ai.agents.validation_agent import ValidationAgent
from claim360ai.models.claim import Claim, ClaimType

from .conftest import make_claim


@pytest.fixture
def agent():
    return ValidationAgent()


class TestValidationAgentValid:
    def test_valid_claim_passes(self, agent):
        claim = make_claim()
        result = agent.run(claim)
        assert result.is_valid
        assert result.errors == []

    def test_valid_claim_no_warnings_by_default(self, agent):
        claim = make_claim()
        result = agent.run(claim)
        assert not result.has_warnings


class TestValidationAgentRequiredFields:
    def test_missing_claim_id(self, agent):
        claim = make_claim(claim_id="")
        result = agent.run(claim)
        assert not result.is_valid
        assert any("claim_id" in e for e in result.errors)

    def test_missing_policy_id(self, agent):
        claim = make_claim(policy_id="")
        result = agent.run(claim)
        assert not result.is_valid

    def test_missing_claimant_email(self, agent):
        claim = make_claim(claimant_email="not-an-email")
        result = agent.run(claim)
        assert not result.is_valid

    def test_missing_diagnosis_codes(self, agent):
        claim = make_claim(diagnosis_codes=[])
        result = agent.run(claim)
        assert not result.is_valid
        assert any("diagnosis" in e.lower() for e in result.errors)

    def test_missing_procedure_codes(self, agent):
        claim = make_claim(procedure_codes=[])
        result = agent.run(claim)
        assert not result.is_valid


class TestValidationAgentDates:
    def test_future_service_date_is_invalid(self, agent):
        future = date.today() + timedelta(days=10)
        claim = make_claim(service_date=future, submission_date=datetime.now())
        result = agent.run(claim)
        assert not result.is_valid
        assert any("future" in e.lower() for e in result.errors)

    def test_submission_before_service_is_invalid(self, agent):
        service = date(2025, 6, 15)
        submission = datetime(2025, 6, 1)  # before service
        claim = make_claim(service_date=service, submission_date=submission)
        result = agent.run(claim)
        assert not result.is_valid

    def test_late_filing_exceeds_limit(self, agent):
        service = date(2024, 1, 1)
        # 400 days later
        submission = datetime(2025, 2, 5)
        claim = make_claim(service_date=service, submission_date=submission)
        result = agent.run(claim)
        assert not result.is_valid
        assert any("timely filing" in e.lower() for e in result.errors)

    def test_warning_for_approaching_limit(self, agent):
        service = date(2025, 1, 1)
        # 200 days later (> 180, < 365)
        submission = datetime(2025, 7, 20)
        claim = make_claim(service_date=service, submission_date=submission)
        result = agent.run(claim)
        assert result.is_valid  # still valid but with warning
        assert result.has_warnings


class TestValidationAgentCodes:
    def test_invalid_icd10_code_is_error(self, agent):
        claim = make_claim(diagnosis_codes=["999"])  # no leading letter
        result = agent.run(claim)
        assert not result.is_valid

    def test_invalid_cpt_produces_warning_not_error(self, agent):
        claim = make_claim(procedure_codes=["ABCDEF"])  # 6 chars
        result = agent.run(claim)
        # Procedure code issues are warnings, not errors
        assert result.has_warnings

    def test_zero_billed_amount(self, agent):
        claim = make_claim(billed_amount=0.0)
        result = agent.run(claim)
        assert not result.is_valid

    def test_negative_billed_amount(self, agent):
        claim = make_claim(billed_amount=-50.0)
        result = agent.run(claim)
        assert not result.is_valid
