"""Coverage Agent - checks whether the claim is covered under the policy."""

from __future__ import annotations

import logging

from claim360ai.models.claim import Claim, ClaimType
from claim360ai.models.claim import PolicyCoverage
from claim360ai.models.review import CoverageCheckResult

logger = logging.getLogger(__name__)


class CoverageAgent:
    """Agent responsible for verifying claim coverage under the associated policy.

    Coverage logic:
    - Confirms the policy is active on the service date
    - Checks whether the claimed service type is covered
    - Checks for procedure-level exclusions
    - Calculates patient responsibility (deductible, coinsurance, copay)
    - Enforces annual benefit limits
    """

    def run(self, claim: Claim, policy: PolicyCoverage) -> CoverageCheckResult:
        """Run coverage checks and return a CoverageCheckResult."""
        logger.info("CoverageAgent: checking coverage for claim %s", claim.claim_id)

        coverage_notes: list[str] = []
        exclusion_reasons: list[str] = []

        # 1. Policy must be active on service date
        if not self._is_policy_active_on_service_date(claim, policy):
            return CoverageCheckResult(
                is_covered=False,
                exclusion_reasons=[
                    f"Policy {policy.policy_id} was not active on service date "
                    f"{claim.service_date}"
                ],
                details={"policy_id": policy.policy_id},
            )

        # 2. Check that the policy belongs to this claimant
        if policy.policy_holder_id != claim.claimant_id:
            exclusion_reasons.append(
                f"Policy holder ID {policy.policy_holder_id} does not match "
                f"claimant ID {claim.claimant_id}"
            )
            return CoverageCheckResult(
                is_covered=False,
                exclusion_reasons=exclusion_reasons,
            )

        # 3. Claim type / service coverage
        claim_type_covered = self._check_claim_type_covered(
            claim, policy, exclusion_reasons, coverage_notes
        )

        # 4. Procedure-level exclusions
        excluded_procedures = self._check_procedure_exclusions(claim, policy)
        if excluded_procedures:
            exclusion_reasons.append(
                f"Procedure(s) excluded from coverage: "
                f"{', '.join(excluded_procedures)}"
            )

        if exclusion_reasons:
            return CoverageCheckResult(
                is_covered=False,
                exclusion_reasons=exclusion_reasons,
                coverage_notes=coverage_notes,
                details={"policy_id": policy.policy_id},
            )

        if not claim_type_covered:
            return CoverageCheckResult(
                is_covered=False,
                exclusion_reasons=exclusion_reasons,
                coverage_notes=coverage_notes,
            )

        # 5. Calculate covered amount and patient responsibility
        covered_amount, patient_responsibility, calc_notes = self._calculate_benefit(
            claim, policy
        )
        coverage_notes.extend(calc_notes)

        logger.info(
            "CoverageAgent: claim %s covered_amount=%.2f patient_responsibility=%.2f",
            claim.claim_id,
            covered_amount,
            patient_responsibility,
        )
        return CoverageCheckResult(
            is_covered=True,
            covered_amount=covered_amount,
            patient_responsibility=patient_responsibility,
            coverage_notes=coverage_notes,
            details={"policy_id": policy.policy_id},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_policy_active_on_service_date(
        self, claim: Claim, policy: PolicyCoverage
    ) -> bool:
        return policy.effective_date <= claim.service_date <= policy.expiration_date

    def _check_claim_type_covered(
        self,
        claim: Claim,
        policy: PolicyCoverage,
        exclusion_reasons: list[str],
        coverage_notes: list[str],
    ) -> bool:
        service_name = claim.claim_type.value.lower()
        covered = any(
            s.lower() == service_name or s.lower() == "all"
            for s in policy.covered_services
        )
        if not covered:
            exclusion_reasons.append(
                f"Service type '{claim.claim_type.value}' is not covered under "
                f"policy {policy.policy_id}"
            )
        else:
            coverage_notes.append(
                f"Service type '{claim.claim_type.value}' is covered"
            )
        return covered

    def _check_procedure_exclusions(
        self, claim: Claim, policy: PolicyCoverage
    ) -> list[str]:
        excluded = []
        for code in claim.procedure_codes:
            if code.upper() in [e.upper() for e in policy.exclusions]:
                excluded.append(code)
        return excluded

    def _calculate_benefit(
        self, claim: Claim, policy: PolicyCoverage
    ) -> tuple[float, float, list[str]]:
        """Calculate the covered amount and patient responsibility."""
        notes: list[str] = []
        billed = claim.billed_amount

        # Check annual limit for this service type
        service_key = claim.claim_type.value
        if service_key in policy.coverage_limits:
            limit = policy.coverage_limits[service_key]
            if billed > limit:
                notes.append(
                    f"Billed amount ${billed:.2f} exceeds annual limit "
                    f"${limit:.2f} for {service_key}"
                )
                billed = limit

        # Apply deductible
        remaining_deductible = policy.remaining_deductible
        deductible_applied = min(remaining_deductible, billed)
        after_deductible = billed - deductible_applied
        if deductible_applied > 0:
            notes.append(
                f"Deductible applied: ${deductible_applied:.2f} (remaining deductible "
                f"was ${remaining_deductible:.2f})"
            )

        # Apply out-of-pocket maximum
        remaining_oop = policy.remaining_out_of_pocket
        if remaining_oop <= 0:
            # OOP max already met — plan pays 100%
            covered_amount = after_deductible
            patient_responsibility = deductible_applied
            notes.append(
                "Out-of-pocket maximum has been met; plan covers remaining balance"
            )
            return covered_amount, patient_responsibility, notes

        # Apply coinsurance/copay
        if policy.coinsurance_rate > 0:
            patient_coinsurance = after_deductible * policy.coinsurance_rate
            plan_coinsurance = after_deductible * (1 - policy.coinsurance_rate)
            notes.append(
                f"Coinsurance: patient pays {policy.coinsurance_rate * 100:.0f}% "
                f"(${patient_coinsurance:.2f}), plan pays ${plan_coinsurance:.2f}"
            )
        else:
            patient_coinsurance = 0.0
            plan_coinsurance = after_deductible

        copay = policy.copay
        if copay > 0:
            notes.append(f"Copay: ${copay:.2f}")

        patient_responsibility = deductible_applied + patient_coinsurance + copay
        # Patient responsibility capped at remaining OOP max
        if patient_responsibility > remaining_oop:
            patient_responsibility = remaining_oop
            notes.append(
                f"Patient responsibility capped at remaining out-of-pocket max "
                f"${remaining_oop:.2f}"
            )

        covered_amount = billed - patient_responsibility
        covered_amount = max(0.0, covered_amount)
        return covered_amount, patient_responsibility, notes
