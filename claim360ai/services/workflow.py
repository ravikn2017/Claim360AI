"""Agentic AI workflow orchestrator for claims adjudication."""

from __future__ import annotations

import logging
from typing import Callable

from claim360ai.agents.adjudication_agent import AdjudicationAgent
from claim360ai.agents.communication_agent import CommunicationAgent, NotificationChannel
from claim360ai.agents.coverage_agent import CoverageAgent
from claim360ai.agents.validation_agent import ValidationAgent
from claim360ai.models.claim import Claim, PolicyCoverage
from claim360ai.models.review import ClaimReviewResult

logger = logging.getLogger(__name__)

# Type alias for a hook that receives intermediate results
WorkflowHook = Callable[[str, object], None]


class ClaimsAdjudicationWorkflow:
    """Orchestrates the end-to-end agentic AI workflow for claims adjudication.

    Workflow steps:
    1. **Validation Agent** – verifies claim validity and accuracy
    2. **Coverage Agent** – checks policy coverage eligibility
    3. **Adjudication Agent** – renders the adjudication decision
    4. **Communication Agent** – notifies the claimant of the outcome

    Each step is performed by a dedicated agent. The orchestrator wires them
    together and propagates context between steps.

    Args:
        notification_channel: Optional custom notification channel.
        hooks: Optional mapping of step names to hook callables for
               observability (logging, audit, metrics, etc.).
    """

    STEP_VALIDATION = "validation"
    STEP_COVERAGE = "coverage"
    STEP_ADJUDICATION = "adjudication"
    STEP_COMMUNICATION = "communication"

    def __init__(
        self,
        notification_channel: NotificationChannel | None = None,
        hooks: dict[str, WorkflowHook] | None = None,
    ) -> None:
        self._validation_agent = ValidationAgent()
        self._coverage_agent = CoverageAgent()
        self._adjudication_agent = AdjudicationAgent()
        self._communication_agent = CommunicationAgent(
            channel=notification_channel
        )
        self._hooks: dict[str, WorkflowHook] = hooks or {}

    def process(
        self, claim: Claim, policy: PolicyCoverage
    ) -> ClaimReviewResult:
        """Process a claim through the full adjudication workflow.

        Args:
            claim: The claim to adjudicate.
            policy: The policy against which the claim is evaluated.

        Returns:
            ClaimReviewResult containing the adjudication decision and all
            intermediate results.
        """
        logger.info(
            "ClaimsAdjudicationWorkflow: starting workflow for claim %s",
            claim.claim_id,
        )

        # Step 1 – Validation
        validation_result = self._validation_agent.run(claim)
        self._invoke_hook(self.STEP_VALIDATION, validation_result)

        # Step 2 – Coverage (run regardless of validation to surface all issues)
        coverage_result = self._coverage_agent.run(claim, policy)
        self._invoke_hook(self.STEP_COVERAGE, coverage_result)

        # Step 3 – Adjudication
        review_result = self._adjudication_agent.run(
            claim, validation_result, coverage_result
        )
        self._invoke_hook(self.STEP_ADJUDICATION, review_result)

        # Step 4 – Communication
        self._communication_agent.run(claim, review_result)
        self._invoke_hook(self.STEP_COMMUNICATION, review_result)

        logger.info(
            "ClaimsAdjudicationWorkflow: completed workflow for claim %s "
            "decision=%s",
            claim.claim_id,
            review_result.decision.value,
        )
        return review_result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _invoke_hook(self, step: str, result: object) -> None:
        hook = self._hooks.get(step)
        if hook:
            try:
                hook(step, result)
            except Exception:
                logger.exception(
                    "Hook for step '%s' raised an exception", step
                )
