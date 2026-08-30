from claim360.adapters.store import load_json
from claim360.models.schemas import PolicySnippet


class FixturePolicySnippetAdapter:
    def snippets(self, refs: list[str]) -> list[PolicySnippet]:
        wanted = set(refs)
        return [
            PolicySnippet.model_validate(row)
            for row in load_json("policies.json")
            if row["ref"] in wanted
        ]
