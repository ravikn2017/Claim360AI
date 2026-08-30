import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from claim360.config import Settings, get_settings
from claim360.models.orm import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_specialist_user(db: Session, settings: Settings | None = None) -> User | None:
    settings = settings or get_settings()
    if not settings.specialist_email or not settings.specialist_password:
        return None

    existing = db.scalar(select(User).where(User.email == settings.specialist_email))
    if existing is not None:
        return existing

    user = User(
        email=settings.specialist_email,
        password_hash=hash_password(settings.specialist_password),
        role="specialist",
    )
    db.add(user)
    db.flush()
    return user


if __name__ == "__main__":
    from claim360.db import session_scope

    with session_scope() as db:
        user = seed_specialist_user(db)
        if user is None:
            print("Skipped: set SPECIALIST_EMAIL and SPECIALIST_PASSWORD")
        else:
            print(f"Seeded specialist {user.email}")
