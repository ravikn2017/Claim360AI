import json
from functools import lru_cache
from typing import Any

from claim360.adapters.paths import fixtures_dir


@lru_cache(maxsize=16)
def load_json(name: str) -> Any:
    path = fixtures_dir() / name
    return json.loads(path.read_text(encoding="utf-8"))
