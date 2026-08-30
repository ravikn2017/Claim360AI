"""Tests for CoverageAgent."""

from __future__ import annotations

from datetime import date

import pytest

from claim360ai.agents.coverage_agent import CoverageAgent
from claim360ai.models.claim import ClaimType

from .conftest import make_claim, make_policy


@pytest.fixture
def agent():
    return CoverageAgent()


class TestCoverageAgentEligibility:
    def test_covered_claim_returns_is_covered_true(self, agent):
        claim = make_claim()
        policy = make_policy()
        result = agent.run(claim, policy)
        assert result.is_covered

    def test_expired_policy_not_covered(self, agent):
        claim = make_claim(service_date=date(2025, 6, 15))
        policy = make_policy(
            effective_date=date(2024, 1, 1),
            expiration_date=date(2025, 1, 1),  # expired before service
        )
        result = agent.run(claim, policy)
        assert not result.is_covered
        assert any("active" in r.lower() or "not active" in r.lower() or "active" in r.lower() for r in result.exclusion_reasons)

    def test_policy_holder_mismatch(self, agent):
        claim = make_claim(claimant_id="WRONG-ID")
        policy = make_policy(policy_holder_id="CLM-001")
        result = agent.run(claim, policy)
        assert not result.is_covered

    def test_uncovered_service_type(self, agent):
        claim = make_claim(claim_type=ClaimType.VISION)
        policy = make_policy(covered_services=["medical", "dental"])
        result = agent.run(claim, policy)
        assert not result.is_covered

    def test_excluded_procedure(self, agent):
        claim = make_claim(procedure_codes=["99213", "X1234"])
        policy = make_policy(exclusions=["X1234"])
        result = agent.run(claim, policy)
        assert not result.is_covered


class TestCoverageAgentBenefitCalculation:
    def test_approved_amount_less_than_billed_with_copay_coinsurance(self, agent):
        claim = make_claim(billed_amount=200.0)
        # deductible already met, 20% coinsurance, $20 copay
        policy = make_policy(
            deductible_met=500.0,
            annual_deductible=500.0,
            coinsurance_rate=0.2,
            copay=20.0,
        )
        result = agent.run(claim, policy)
        assert result.is_covered
        # patient pays: 20% of 200 + $20 copay = $40 + $20 = $60
        assert abs(result.patient_responsibility - 60.0) < 0.01
        assert abs(result.covered_amount - 140.0) < 0.01

    def test_oop_max_met_plan_pays_all(self, agent):
        claim = make_claim(billed_amount=200.0)
        policy = make_policy(
            annual_out_of_pocket_max=3000.0,
            out_of_pocket_met=3000.0,  # OOP already met
            annual_deductible=500.0,
            deductible_met=500.0,
            coinsurance_rate=0.2,
            copay=0.0,
        )
        result = agent.run(claim, policy)
        assert result.is_covered
        assert abs(result.covered_amount - 200.0) < 0.01

    def test_annual_limit_caps_covered_amount(self, agent):
        claim = make_claim(billed_amount=200_000.0)
        policy = make_policy(
            annual_deductible=0.0,
            deductible_met=0.0,
            coinsurance_rate=0.0,
            copay=0.0,
            coverage_limits={"MEDICAL": 100_000.0},
        )
        result = agent.run(claim, policy)
        assert result.is_covered
        # covered amount should not exceed limit
        assert result.covered_amount <= 100_000.0
