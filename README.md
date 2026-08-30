# Claim360AI

Claim360AI is an **agentic AI workflow** for insurance claims adjudication and communication of review outcomes.

## Overview

The system reviews each claim for:
- **Validity** – required fields, dates, diagnosis/procedure code formats
- **Accuracy** – timely filing, billed amount sanity, provider NPI
- **Coverage** – active policy, service type eligibility, exclusions, benefit calculation

The workflow is orchestrated through four specialised agents:

| Agent | Responsibility |
|---|---|
| `ValidationAgent` | Validates claim completeness and accuracy |
| `CoverageAgent` | Checks policy coverage and calculates benefits |
| `AdjudicationAgent` | Renders the final adjudication decision |
| `CommunicationAgent` | Notifies the claimant of the outcome |

## Project Structure

```
claim360ai/
  agents/
    validation_agent.py      # Validity & accuracy checks
    coverage_agent.py        # Coverage eligibility & benefit calculation
    adjudication_agent.py    # Final decision engine
    communication_agent.py   # Outcome notification (email / SMS)
  models/
    claim.py                 # Claim, PolicyCoverage data models
    review.py                # ValidationResult, CoverageCheckResult, ClaimReviewResult
  services/
    workflow.py              # ClaimsAdjudicationWorkflow orchestrator
tests/
  conftest.py                # Shared test fixtures
  test_validation_agent.py
  test_coverage_agent.py
  test_workflow.py
```

## Quick Start

```python
from datetime import date, datetime
from claim360ai.models.claim import Claim, ClaimType, PolicyCoverage
from claim360ai.services.workflow import ClaimsAdjudicationWorkflow

policy = PolicyCoverage(
    policy_id="POL-001",
    policy_holder_id="MBR-001",
    policy_holder_name="Jane Doe",
    effective_date=date(2024, 1, 1),
    expiration_date=date(2026, 12, 31),
    covered_services=["medical"],
    annual_deductible=500.0,
    deductible_met=500.0,
    annual_out_of_pocket_max=3000.0,
    out_of_pocket_met=0.0,
    copay=20.0,
    coinsurance_rate=0.2,
)

claim = Claim(
    claim_id="CLM-2025-001",
    policy_id="POL-001",
    claimant_id="MBR-001",
    claimant_name="Jane Doe",
    claimant_email="jane@example.com",
    claim_type=ClaimType.MEDICAL,
    service_date=date(2025, 6, 15),
    submission_date=datetime(2025, 6, 20),
    provider_name="City Medical Center",
    provider_npi="1234567890",
    diagnosis_codes=["Z00.00"],
    procedure_codes=["99213"],
    billed_amount=200.0,
)

workflow = ClaimsAdjudicationWorkflow()
result = workflow.process(claim, policy)
print(result.decision, result.approved_amount)
```

## Running Tests

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

## Workflow Decisions

| Outcome | Conditions |
|---|---|
| `APPROVED` | Valid claim, covered, fully approved |
| `PARTIALLY_APPROVED` | Valid claim, covered, partial coverage only |
| `DENIED` | Invalid claim OR not covered by policy |
| `PENDING_INFO` | Valid claim, covered, but validation warnings require human review |
