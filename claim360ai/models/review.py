"""Review result data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AdjudicationDecision(str, Enum):
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    DENIED = "DENIED"
    PENDING_INFO = "PENDING_INFO"


@dataclass
class ValidationResult:
    """Result of claim validity and accuracy validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


@dataclass
class CoverageCheckResult:
    """Result of coverage eligibility check."""

    is_covered: bool
    covered_amount: float = 0.0
    patient_responsibility: float = 0.0
    coverage_notes: list[str] = field(default_factory=list)
    exclusion_reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimReviewResult:
    """Aggregated result of the full claim review workflow."""

    claim_id: str
    decision: AdjudicationDecision
    validation: ValidationResult
    coverage: CoverageCheckResult
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    adjudicator_notes: str = ""
    approved_amount: float = 0.0
    denial_reasons: list[str] = field(default_factory=list)
    notification_sent: bool = False
    notification_channel: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "decision": self.decision.value,
            "reviewed_at": self.reviewed_at.isoformat(),
            "adjudicator_notes": self.adjudicator_notes,
            "approved_amount": self.approved_amount,
            "denial_reasons": self.denial_reasons,
            "notification_sent": self.notification_sent,
            "notification_channel": self.notification_channel,
            "validation": {
                "is_valid": self.validation.is_valid,
                "errors": self.validation.errors,
                "warnings": self.validation.warnings,
            },
            "coverage": {
                "is_covered": self.coverage.is_covered,
                "covered_amount": self.coverage.covered_amount,
                "patient_responsibility": self.coverage.patient_responsibility,
                "coverage_notes": self.coverage.coverage_notes,
                "exclusion_reasons": self.coverage.exclusion_reasons,
            },
        }
