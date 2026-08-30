from datetime import date

from claim360.adapters.store import load_json
from claim360.models.schemas import EligibilityRecord


def _unknown(member_id: str, notes: str) -> EligibilityRecord:
    return EligibilityRecord(
        member_id=member_id,
        found=False,
        status="unknown",
        active_on_dos=False,
        notes=notes,
    )


class FixtureEligibilityAdapter:
    def get_eligibility(self, member_id: str, dos: date) -> EligibilityRecord:
        rows = load_json("eligibility.json")
        match = next((row for row in rows if row["member_id"] == member_id), None)
        if match is None:
            return _unknown(member_id, "No eligibility record for member")

        start = date.fromisoformat(match["effective_from"])
        end = date.fromisoformat(match["effective_to"])
        active_on_dos = start <= dos <= end
        return EligibilityRecord(
            member_id=member_id,
            found=True,
            status=match["status"],
            plan_id=match.get("plan_id"),
            effective_from=start,
            effective_to=end,
            covered_procedures=list(match.get("covered_procedures", [])),
            covered_diagnoses=list(match.get("covered_diagnoses", [])),
            policy_refs=list(match.get("policy_refs", [])),
            active_on_dos=active_on_dos,
            notes="" if active_on_dos else "Date of service is outside the eligibility window",
        )
