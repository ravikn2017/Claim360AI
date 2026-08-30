"""Adjudication Agent - makes the final claim decision."""

from __future__ import annotations

import logging

from claim360ai.models.claim import Claim, ClaimStatus
from claim360ai.models.review import (
    AdjudicationDecision,
    ClaimReviewResult,
    CoverageCheckResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class AdjudicationAgent:
    """Agent responsible for making the final adjudication decision on a claim.

    Decision logic:
    - DENIED if validation fails (invalid claim)
    - DENIED if coverage check fails
    - APPROVED if fully covered
    - PARTIALLY_APPROVED if only a portion is covered
    - PENDING_INFO if validation has warnings that need human review
    """

    def run(
        self,
        claim: Claim,
        validation: ValidationResult,
        coverage: CoverageCheckResult,
    ) -> ClaimReviewResult:
        """Adjudicate the claim and return a ClaimReviewResult."""
        logger.info("AdjudicationAgent: adjudicating claim %s", claim.claim_id)

        decision, denial_reasons, approved_amount, notes = self._decide(
            claim, validation, coverage
        )

        # Update claim status to reflect decision
        claim.status = self._map_decision_to_status(decision)

        result = ClaimReviewResult(
            claim_id=claim.claim_id,
            decision=decision,
            validation=validation,
            coverage=coverage,
            adjudicator_notes=notes,
            approved_amount=approved_amount,
            denial_reasons=denial_reasons,
        )

        logger.info(
            "AdjudicationAgent: claim %s decision=%s approved_amount=%.2f",
            claim.claim_id,
            decision.value,
            approved_amount,
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _decide(
        self,
        claim: Claim,
        validation: ValidationResult,
        coverage: CoverageCheckResult,
    ) -> tuple[AdjudicationDecision, list[str], float, str]:
        denial_reasons: list[str] = []
        notes_parts: list[str] = []

        # Hard stop on validation errors
        if not validation.is_valid:
            denial_reasons.extend(validation.errors)
            return (
                AdjudicationDecision.DENIED,
                denial_reasons,
                0.0,
                "Claim denied due to validation errors.",
            )

        # Collect validation warnings — flag for pending review
        if validation.has_warnings:
            notes_parts.append(
                "Validation warnings present: " + "; ".join(validation.warnings)
            )

        # Coverage denial
        if not coverage.is_covered:
            denial_reasons.extend(coverage.exclusion_reasons)
            return (
                AdjudicationDecision.DENIED,
                denial_reasons,
                0.0,
                "Claim denied: not covered under policy.",
            )

        approved_amount = coverage.covered_amount

        if approved_amount <= 0:
            denial_reasons.append("No covered amount after applying benefits")
            return (
                AdjudicationDecision.DENIED,
                denial_reasons,
                0.0,
                "Claim denied: zero covered amount after benefit calculation.",
            )

        # Determine full vs partial approval
        if abs(approved_amount - claim.billed_amount) < 0.01:
            decision = AdjudicationDecision.APPROVED
            notes_parts.append(
                f"Claim fully approved for ${approved_amount:.2f}."
            )
        else:
            decision = AdjudicationDecision.PARTIALLY_APPROVED
            notes_parts.append(
                f"Claim partially approved: ${approved_amount:.2f} of "
                f"${claim.billed_amount:.2f} billed."
            )

        # Elevate to PENDING_INFO when there are warnings
        if validation.has_warnings and decision != AdjudicationDecision.DENIED:
            decision = AdjudicationDecision.PENDING_INFO
            notes_parts.append(
                "Decision set to PENDING_INFO pending human review of warnings."
            )

        return decision, denial_reasons, approved_amount, " ".join(notes_parts)

    @staticmethod
    def _map_decision_to_status(decision: AdjudicationDecision) -> ClaimStatus:
        mapping = {
            AdjudicationDecision.APPROVED: ClaimStatus.APPROVED,
            AdjudicationDecision.PARTIALLY_APPROVED: ClaimStatus.PARTIALLY_APPROVED,
            AdjudicationDecision.DENIED: ClaimStatus.DENIED,
            AdjudicationDecision.PENDING_INFO: ClaimStatus.PENDING_INFO,
        }
        return mapping[decision]
