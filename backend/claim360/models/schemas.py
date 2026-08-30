from datetime import date

from pydantic import BaseModel, Field

from claim360.models.enums import (
    FieldFindingStatus,
    FraudRiskLevel,
    MedNecDetermination,
    PolicyOutcome,
)

SCHEMA_VERSION = "1.0"


class ClaimPayload(BaseModel):
    portal_claim_ref: str
    member_external_id: str
    provider_npi: str
    date_of_service: date
    diagnosis_codes: list[str]
    procedure_codes: list[str]
    place_of_service: str
    billed_amount_cents: int = Field(ge=0)
    units: int = Field(ge=1)
    service_description: str


class FieldFinding(BaseModel):
    field: str
    status: FieldFindingStatus
    message: str


class PolicyOutput(BaseModel):
    outcome: PolicyOutcome
    field_findings: list[FieldFinding]
    policy_refs: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class FraudIndicator(BaseModel):
    code: str
    detail: str


class FraudOutput(BaseModel):
    risk_level: FraudRiskLevel
    risk_score: int = Field(ge=0, le=100)
    indicators: list[FraudIndicator]
    confidence: float = Field(ge=0.0, le=1.0)


class MedNecOutput(BaseModel):
    determination: MedNecDetermination
    guideline_refs: list[str]
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class LetterDraft(BaseModel):
    subject: str
    body: str


class EligibilityRecord(BaseModel):
    """Adapter output. `found=False` / status `unknown` → Policy `needs_clarification`."""

    member_id: str
    found: bool
    status: str
    plan_id: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    covered_procedures: list[str] = Field(default_factory=list)
    covered_diagnoses: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    active_on_dos: bool = False
    notes: str = ""


class HistoryClaim(BaseModel):
    portal_claim_ref: str
    date_of_service: date
    provider_npi: str
    diagnosis_codes: list[str]
    procedure_codes: list[str]
    billed_amount_cents: int
    status: str = "paid"


class MemberHistory(BaseModel):
    member_id: str
    found: bool
    claims: list[HistoryClaim] = Field(default_factory=list)


class GuidelineHit(BaseModel):
    guideline_id: str
    title: str
    diagnosis_codes: list[str]
    procedure_codes: list[str]
    determination_hint: str
    snippet: str


class GuidelineHits(BaseModel):
    hits: list[GuidelineHit] = Field(default_factory=list)


class PolicySnippet(BaseModel):
    ref: str
    title: str
    text: str
