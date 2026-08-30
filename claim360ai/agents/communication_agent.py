"""Communication Agent - sends review outcome notifications to claimants."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from string import Template

from claim360ai.models.claim import Claim
from claim360ai.models.review import AdjudicationDecision, ClaimReviewResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Message templates
# ---------------------------------------------------------------------------

_SUBJECT_TEMPLATES = {
    AdjudicationDecision.APPROVED: "Your Claim $claim_id Has Been Approved",
    AdjudicationDecision.PARTIALLY_APPROVED: (
        "Your Claim $claim_id Has Been Partially Approved"
    ),
    AdjudicationDecision.DENIED: "Your Claim $claim_id Has Been Denied",
    AdjudicationDecision.PENDING_INFO: (
        "Your Claim $claim_id Requires Additional Information"
    ),
}

_BODY_TEMPLATES = {
    AdjudicationDecision.APPROVED: Template(
        """Dear $claimant_name,

We are pleased to inform you that your insurance claim (ID: $claim_id) for
services rendered on $service_date has been APPROVED.

Approved Amount : $$${approved_amount}
Billed Amount   : $$${billed_amount}

$coverage_notes

If you have any questions, please contact our claims support team.

Sincerely,
Claim360AI Adjudication Team
"""
    ),
    AdjudicationDecision.PARTIALLY_APPROVED: Template(
        """Dear $claimant_name,

Your insurance claim (ID: $claim_id) for services rendered on $service_date
has been PARTIALLY APPROVED.

Approved Amount        : $$${approved_amount}
Billed Amount          : $$${billed_amount}
Patient Responsibility : $$${patient_responsibility}

$coverage_notes

If you believe this decision is in error or you have additional documentation,
please contact our claims support team within 30 days.

Sincerely,
Claim360AI Adjudication Team
"""
    ),
    AdjudicationDecision.DENIED: Template(
        """Dear $claimant_name,

We regret to inform you that your insurance claim (ID: $claim_id) for
services rendered on $service_date has been DENIED.

Reason(s) for Denial:
$denial_reasons

You have the right to appeal this decision. Please contact our claims support
team within 60 days if you wish to file an appeal.

Sincerely,
Claim360AI Adjudication Team
"""
    ),
    AdjudicationDecision.PENDING_INFO: Template(
        """Dear $claimant_name,

Your insurance claim (ID: $claim_id) for services rendered on $service_date
is currently PENDING ADDITIONAL INFORMATION.

Notes:
$adjudicator_notes

Please provide the requested information within 14 days to avoid claim denial.

Sincerely,
Claim360AI Adjudication Team
"""
    ),
}


# ---------------------------------------------------------------------------
# Notification channel abstraction
# ---------------------------------------------------------------------------


class NotificationChannel(ABC):
    """Abstract notification channel."""

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> bool:
        """Send a notification. Returns True if successful."""


class EmailChannel(NotificationChannel):
    """Email notification channel (logs output; replace with SMTP/SES in production)."""

    def send(self, recipient: str, subject: str, body: str) -> bool:
        logger.info(
            "EMAIL → %s\nSubject: %s\n%s", recipient, subject, body
        )
        return True


class SMSChannel(NotificationChannel):
    """SMS notification channel (logs output; replace with Twilio/SNS in production)."""

    def send(self, recipient: str, subject: str, body: str) -> bool:
        short_message = f"{subject}\n{body[:160]}"
        logger.info("SMS → %s\n%s", recipient, short_message)
        return True


# ---------------------------------------------------------------------------
# Communication Agent
# ---------------------------------------------------------------------------


class CommunicationAgent:
    """Agent responsible for communicating the adjudication outcome to claimants.

    Supports pluggable notification channels (default: email).
    """

    def __init__(self, channel: NotificationChannel | None = None) -> None:
        self._channel: NotificationChannel = channel or EmailChannel()

    def run(self, claim: Claim, review_result: ClaimReviewResult) -> bool:
        """Send the review outcome notification. Returns True on success."""
        logger.info(
            "CommunicationAgent: sending notification for claim %s", claim.claim_id
        )

        subject, body = self._compose_message(claim, review_result)
        success = self._channel.send(claim.claimant_email, subject, body)

        review_result.notification_sent = success
        review_result.notification_channel = type(self._channel).__name__

        if success:
            logger.info(
                "CommunicationAgent: notification sent for claim %s via %s",
                claim.claim_id,
                review_result.notification_channel,
            )
        else:
            logger.warning(
                "CommunicationAgent: failed to send notification for claim %s",
                claim.claim_id,
            )

        return success

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compose_message(
        self, claim: Claim, review_result: ClaimReviewResult
    ) -> tuple[str, str]:
        decision = review_result.decision
        subject_tmpl = _SUBJECT_TEMPLATES[decision]
        body_tmpl = _BODY_TEMPLATES[decision]

        subject = Template(subject_tmpl).safe_substitute(claim_id=claim.claim_id)

        coverage_notes_text = (
            "\n".join(review_result.coverage.coverage_notes)
            if review_result.coverage.coverage_notes
            else ""
        )
        denial_reasons_text = (
            "\n".join(
                f"  - {r}" for r in review_result.denial_reasons
            )
            if review_result.denial_reasons
            else "  - See adjudicator notes"
        )

        body = body_tmpl.safe_substitute(
            claimant_name=claim.claimant_name,
            claim_id=claim.claim_id,
            service_date=str(claim.service_date),
            approved_amount=f"{review_result.approved_amount:.2f}",
            billed_amount=f"{claim.billed_amount:.2f}",
            patient_responsibility=f"{review_result.coverage.patient_responsibility:.2f}",
            coverage_notes=coverage_notes_text,
            denial_reasons=denial_reasons_text,
            adjudicator_notes=review_result.adjudicator_notes,
        )

        return subject, body
