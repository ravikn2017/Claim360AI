from claim360.adapters.store import load_json
from claim360.models.schemas import GuidelineHit, GuidelineHits


class FixtureGuidelineAdapter:
    def match(self, dx: list[str], px: list[str]) -> GuidelineHits:
        dx_set = set(dx)
        px_set = set(px)
        hits: list[GuidelineHit] = []
        for row in load_json("guidelines.json"):
            if dx_set & set(row["diagnosis_codes"]) and px_set & set(row["procedure_codes"]):
                hits.append(
                    GuidelineHit(
                        guideline_id=row["id"],
                        title=row["title"],
                        diagnosis_codes=list(row["diagnosis_codes"]),
                        procedure_codes=list(row["procedure_codes"]),
                        determination_hint=row["determination_hint"],
                        snippet=row["snippet"],
                    )
                )
        return GuidelineHits(hits=hits)
