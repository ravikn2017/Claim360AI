from claim360.adapters.store import load_json
from claim360.models.schemas import HistoryClaim, MemberHistory


class FixtureHistoryAdapter:
    def get_claims(self, member_id: str) -> MemberHistory:
        by_member = load_json("claims_history.json")
        rows = by_member.get(member_id)
        if rows is None:
            return MemberHistory(member_id=member_id, found=False, claims=[])
        return MemberHistory(
            member_id=member_id,
            found=True,
            claims=[HistoryClaim.model_validate(row) for row in rows],
        )
