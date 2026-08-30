import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from claim360.config import get_settings
from claim360.db import ping_database
from claim360.models.orm import Base


def postgres_reachable() -> bool:
    try:
        ping_database()
        return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not postgres_reachable(),
    reason="Postgres not reachable with DATABASE_URL (create role claim360 / database claim360)",
)

SAMPLE_CLAIM = {
    "portal_claim_ref": "CLM-1001",
    "member_external_id": "MEM-001",
    "provider_npi": "1234567890",
    "date_of_service": "2026-06-01",
    "diagnosis_codes": ["M54.5"],
    "procedure_codes": ["97110"],
    "place_of_service": "11",
    "billed_amount_cents": 15000,
    "units": 2,
    "service_description": "Therapeutic exercises",
}


@pytest.fixture()
def db() -> Session:
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
        engine.dispose()
