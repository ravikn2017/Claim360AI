"""Tests for ClaimsAdjudicationWorkflow end-to-end."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from claim360ai.agents.communication_agent import NotificationChannel
from claim360ai.models.review import AdjudicationDecision
from claim360ai.services.workflow import ClaimsAdjudicationWorkflow

from .conftest import make_claim, make_policy


class CapturingChannel(NotificationChannel):
    """Test channel that captures sent notifications."""

    def __init__(self):
        self.sent = []

    def send(self, recipient: str, subject: str, body: str) -> bool:
        self.sent.append({"recipient": recipient, "subject": subject, "body": body})
        return True


@pytest.fixture
def channel():
    return CapturingChannel()


@pytest.fixture
def workflow(channel):
    return ClaimsAdjudicationWorkflow(notification_channel=channel)


class TestWorkflowApproved:
    def test_valid_covered_claim_is_approved(self, workflow, channel):
        claim = make_claim()
        policy = make_policy()
        result = workflow.process(claim, policy)
        assert result.decision in (
            AdjudicationDecision.APPROVED,
            AdjudicationDecision.PARTIALLY_APPROVED,
        )
        assert result.approved_amount > 0
        assert result.notification_sent
        assert len(channel.sent) == 1
        assert "alice@example.com" in channel.sent[0]["recipient"]

    def test_notification_subject_contains_claim_id(self, workflow, channel):
        claim = make_claim()
        policy = make_policy()
        workflow.process(claim, policy)
        subject = channel.sent[0]["subject"]
        assert claim.claim_id in subject


class TestWorkflowDenied:
    def test_invalid_claim_is_denied(self, workflow, channel):
        claim = make_claim(diagnosis_codes=[])  # invalid — no diagnosis codes
        policy = make_policy()
        result = workflow.process(claim, policy)
        assert result.decision == AdjudicationDecision.DENIED
        assert result.approved_amount == 0.0
        assert result.notification_sent

    def test_uncovered_claim_is_denied(self, workflow, channel):
        from claim360ai.models.claim import ClaimType
        claim = make_claim(claim_type=ClaimType.VISION)
        policy = make_policy(covered_services=["medical"])
        result = workflow.process(claim, policy)
        assert result.decision == AdjudicationDecision.DENIED

    def test_expired_policy_denied(self, workflow, channel):
        claim = make_claim(service_date=date(2025, 6, 15))
        policy = make_policy(expiration_date=date(2025, 1, 1))
        result = workflow.process(claim, policy)
        assert result.decision == AdjudicationDecision.DENIED


class TestWorkflowHooks:
    def test_hooks_are_invoked(self, channel):
        steps_seen = []

        def hook(step, result):
            steps_seen.append(step)

        hooks = {
            ClaimsAdjudicationWorkflow.STEP_VALIDATION: hook,
            ClaimsAdjudicationWorkflow.STEP_COVERAGE: hook,
            ClaimsAdjudicationWorkflow.STEP_ADJUDICATION: hook,
            ClaimsAdjudicationWorkflow.STEP_COMMUNICATION: hook,
        }
        wf = ClaimsAdjudicationWorkflow(notification_channel=channel, hooks=hooks)
        claim = make_claim()
        policy = make_policy()
        wf.process(claim, policy)
        assert set(steps_seen) == {
            ClaimsAdjudicationWorkflow.STEP_VALIDATION,
            ClaimsAdjudicationWorkflow.STEP_COVERAGE,
            ClaimsAdjudicationWorkflow.STEP_ADJUDICATION,
            ClaimsAdjudicationWorkflow.STEP_COMMUNICATION,
        }

    def test_faulty_hook_does_not_abort_workflow(self, channel):
        def bad_hook(step, result):
            raise RuntimeError("hook failure")

        wf = ClaimsAdjudicationWorkflow(
            notification_channel=channel,
            hooks={ClaimsAdjudicationWorkflow.STEP_VALIDATION: bad_hook},
        )
        claim = make_claim()
        policy = make_policy()
        result = wf.process(claim, policy)
        # Workflow should complete despite hook error
        assert result is not None
