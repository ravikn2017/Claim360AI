from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def fixtures_dir() -> Path:
    """Repo-root `fixtures/` (data, not a Python package)."""
    return Path(__file__).resolve().parents[3] / "fixtures"
