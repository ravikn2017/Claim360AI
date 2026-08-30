"""Claim data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    DENIED = "DENIED"
    PENDING_INFO = "PENDING_INFO"


class ClaimType(str, Enum):
    MEDICAL = "MEDICAL"
    DENTAL = "DENTAL"
    VISION = "VISION"
    PHARMACY = "PHARMACY"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    EMERGENCY = "EMERGENCY"


@dataclass
class PolicyCoverage:
    """Represents a policy and its coverage details."""

    policy_id: str
    policy_holder_id: str
    policy_holder_name: str
    effective_date: date
    expiration_date: date
    covered_services: list[str] = field(default_factory=list)
    annual_deductible: float = 0.0
    deductible_met: float = 0.0
    annual_out_of_pocket_max: float = 0.0
    out_of_pocket_met: float = 0.0
    copay: float = 0.0
    coinsurance_rate: float = 0.0
    coverage_limits: dict[str, float] = field(default_factory=dict)
    exclusions: list[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        today = date.today()
        return self.effective_date <= today <= self.expiration_date

    @property
    def remaining_deductible(self) -> float:
        return max(0.0, self.annual_deductible - self.deductible_met)

    @property
    def remaining_out_of_pocket(self) -> float:
        return max(0.0, self.annual_out_of_pocket_max - self.out_of_pocket_met)


@dataclass
class Claim:
    """Represents an insurance claim submitted for adjudication."""

    claim_id: str
    policy_id: str
    claimant_id: str
    claimant_name: str
    claimant_email: str
    claim_type: ClaimType
    service_date: date
    submission_date: datetime
    provider_name: str
    provider_npi: str
    diagnosis_codes: list[str] = field(default_factory=list)
    procedure_codes: list[str] = field(default_factory=list)
    billed_amount: float = 0.0
    supporting_documents: list[str] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.SUBMITTED
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "policy_id": self.policy_id,
            "claimant_id": self.claimant_id,
            "claimant_name": self.claimant_name,
            "claimant_email": self.claimant_email,
            "claim_type": self.claim_type.value,
            "service_date": self.service_date.isoformat(),
            "submission_date": self.submission_date.isoformat(),
            "provider_name": self.provider_name,
            "provider_npi": self.provider_npi,
            "diagnosis_codes": self.diagnosis_codes,
            "procedure_codes": self.procedure_codes,
            "billed_amount": self.billed_amount,
            "supporting_documents": self.supporting_documents,
            "status": self.status.value,
            "notes": self.notes,
        }
