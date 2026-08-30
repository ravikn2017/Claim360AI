"""Test fixtures for Claim360AI tests."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from claim360ai.models.claim import Claim, ClaimType, PolicyCoverage


def make_policy(**kwargs) -> PolicyCoverage:
    defaults = dict(
        policy_id="POL-001",
        policy_holder_id="CLM-001",
        policy_holder_name="Alice Smith",
        effective_date=date(2024, 1, 1),
        expiration_date=date(2026, 12, 31),
        covered_services=["medical", "dental", "pharmacy"],
        annual_deductible=500.0,
        deductible_met=500.0,  # already met for simplicity
        annual_out_of_pocket_max=3000.0,
        out_of_pocket_met=0.0,
        copay=20.0,
        coinsurance_rate=0.2,
        coverage_limits={"MEDICAL": 100_000.0},
        exclusions=[],
    )
    defaults.update(kwargs)
    return PolicyCoverage(**defaults)


def make_claim(**kwargs) -> Claim:
    defaults = dict(
        claim_id="CLM-2024-001",
        policy_id="POL-001",
        claimant_id="CLM-001",
        claimant_name="Alice Smith",
        claimant_email="alice@example.com",
        claim_type=ClaimType.MEDICAL,
        service_date=date(2025, 6, 15),
        submission_date=datetime(2025, 6, 20),
        provider_name="General Hospital",
        provider_npi="1234567890",
        diagnosis_codes=["Z00.00"],
        procedure_codes=["99213"],
        billed_amount=200.0,
        supporting_documents=[],
    )
    defaults.update(kwargs)
    return Claim(**defaults)
