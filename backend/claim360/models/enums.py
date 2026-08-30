from enum import StrEnum


class ClaimStatus(StrEnum):
    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    POLICY_RUNNING = "POLICY_RUNNING"
    FRAUD_RUNNING = "FRAUD_RUNNING"
    MEDNEC_RUNNING = "MEDNEC_RUNNING"
    PROPOSED = "PROPOSED"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    ESCALATED = "ESCALATED"
    FINALIZED = "FINALIZED"
    FAILED_ESCALATED = "FAILED_ESCALATED"


class Decision(StrEnum):
    APPROVE = "approve"
    DENY = "deny"
    PARTIAL_APPROVE = "partial_approve"
    PEND = "pend"


class AgentName(StrEnum):
    POLICY = "policy"
    FRAUD = "fraud"
    MEDNEC = "mednec"


class Actor(StrEnum):
    SYSTEM = "system"
    SPECIALIST = "specialist"
    PORTAL = "portal"


class AuditEventType(StrEnum):
    CLAIM_RECEIVED = "claim_received"
    QUEUED = "queued"
    POLICY_COMPLETED = "policy_completed"
    FRAUD_COMPLETED = "fraud_completed"
    MEDNEC_COMPLETED = "mednec_completed"
    DECISION_PROPOSED = "decision_proposed"
    LETTER_DRAFTED = "letter_drafted"
    HUMAN_EDITED = "human_edited"
    HUMAN_APPROVED = "human_approved"
    HUMAN_ESCALATED = "human_escalated"
    DISPOSITION_STUBBED = "disposition_stubbed"
    AGENT_RETRY = "agent_retry"
    AGENT_FAILED = "agent_failed"


class PolicyOutcome(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    PARTIAL = "partial"
    NEEDS_CLARIFICATION = "needs_clarification"


class FieldFindingStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNCLEAR = "unclear"


class FraudRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MedNecDetermination(StrEnum):
    NECESSARY = "necessary"
    NOT_NECESSARY = "not_necessary"
    INSUFFICIENT_INFO = "insufficient_info"
