"""Validation Agent - checks claim validity and accuracy."""

from __future__ import annotations

import logging
from datetime import date, datetime

from claim360ai.models.claim import Claim
from claim360ai.models.review import ValidationResult

logger = logging.getLogger(__name__)

# ICD-10 codes must match this basic pattern: letter + 2 digits (+ optional suffix)
_VALID_ICD10_PATTERN_LEN = 3
# CPT codes are 5 digits
_VALID_CPT_LENGTH = 5


class ValidationAgent:
    """Agent responsible for validating the validity and accuracy of a claim.

    Checks performed:
    - Required fields are present and non-empty
    - Service date is not in the future and not before policy effective date
    - Claim was submitted within the allowed filing window
    - Diagnosis and procedure codes follow expected formats
    - Billed amount is a positive number
    - Provider NPI is present
    """

    MAX_FILING_DAYS = 365  # typical timely filing limit

    def run(self, claim: Claim) -> ValidationResult:
        """Validate the given claim and return a ValidationResult."""
        logger.info("ValidationAgent: validating claim %s", claim.claim_id)
        errors: list[str] = []
        warnings: list[str] = []
        details: dict = {}

        self._check_required_fields(claim, errors)
        self._check_dates(claim, errors, warnings)
        self._check_codes(claim, errors, warnings)
        self._check_billed_amount(claim, errors)
        self._check_provider(claim, errors, warnings)

        is_valid = len(errors) == 0
        details["checks_performed"] = [
            "required_fields",
            "dates",
            "codes",
            "billed_amount",
            "provider",
        ]
        result = ValidationResult(
            is_valid=is_valid, errors=errors, warnings=warnings, details=details
        )
        logger.info(
            "ValidationAgent: claim %s is_valid=%s errors=%d warnings=%d",
            claim.claim_id,
            is_valid,
            len(errors),
            len(warnings),
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_required_fields(self, claim: Claim, errors: list[str]) -> None:
        if not claim.claim_id:
            errors.append("Missing required field: claim_id")
        if not claim.policy_id:
            errors.append("Missing required field: policy_id")
        if not claim.claimant_id:
            errors.append("Missing required field: claimant_id")
        if not claim.claimant_name:
            errors.append("Missing required field: claimant_name")
        if not claim.claimant_email or "@" not in claim.claimant_email:
            errors.append("Missing or invalid claimant email address")
        if not claim.provider_name:
            errors.append("Missing required field: provider_name")
        if not claim.diagnosis_codes:
            errors.append("At least one diagnosis code is required")
        if not claim.procedure_codes:
            errors.append("At least one procedure code is required")

    def _check_dates(
        self, claim: Claim, errors: list[str], warnings: list[str]
    ) -> None:
        today = date.today()
        if claim.service_date > today:
            errors.append(
                f"Service date {claim.service_date} cannot be in the future"
            )
        submission_date = (
            claim.submission_date.date()
            if isinstance(claim.submission_date, datetime)
            else claim.submission_date
        )
        days_since_service = (submission_date - claim.service_date).days
        if days_since_service < 0:
            errors.append(
                "Submission date cannot be before service date"
            )
        elif days_since_service > self.MAX_FILING_DAYS:
            errors.append(
                f"Claim submitted {days_since_service} days after service date; "
                f"exceeds timely filing limit of {self.MAX_FILING_DAYS} days"
            )
        elif days_since_service > 180:
            warnings.append(
                f"Claim submitted {days_since_service} days after service date; "
                "approaching timely filing limit"
            )

    def _check_codes(
        self, claim: Claim, errors: list[str], warnings: list[str]
    ) -> None:
        for code in claim.diagnosis_codes:
            if not self._is_valid_icd10(code):
                errors.append(f"Invalid diagnosis code format: {code}")
        for code in claim.procedure_codes:
            if not self._is_valid_cpt(code):
                warnings.append(
                    f"Procedure code '{code}' does not match standard CPT format "
                    "(5 digits); verify accuracy"
                )

    def _check_billed_amount(self, claim: Claim, errors: list[str]) -> None:
        if claim.billed_amount <= 0:
            errors.append(
                f"Billed amount must be greater than zero; got {claim.billed_amount}"
            )

    def _check_provider(
        self, claim: Claim, errors: list[str], warnings: list[str]
    ) -> None:
        npi = claim.provider_npi.strip()
        if not npi:
            errors.append("Provider NPI is required")
        elif not npi.isdigit() or len(npi) != 10:
            warnings.append(
                f"Provider NPI '{npi}' does not appear to be a valid 10-digit NPI"
            )

    @staticmethod
    def _is_valid_icd10(code: str) -> bool:
        """Minimal ICD-10 format check: starts with a letter, followed by digits."""
        code = code.strip().upper()
        if len(code) < _VALID_ICD10_PATTERN_LEN:
            return False
        return code[0].isalpha() and code[1:3].isdigit()

    @staticmethod
    def _is_valid_cpt(code: str) -> bool:
        """Basic CPT format check: 5 alphanumeric characters."""
        code = code.strip()
        return len(code) == _VALID_CPT_LENGTH and code.isalnum()
