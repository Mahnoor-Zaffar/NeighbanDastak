from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.core.config import get_settings


def _payload(record_number: str) -> dict[str, str]:
    return {
        "record_number": record_number,
        "first_name": "Rate",
        "last_name": "Limited",
        "date_of_birth": "1992-11-11",
        "email": f"{record_number.lower()}@example.com",
        "phone": "+1 555 0404",
        "city": "Lahore",
        "notes": "Rate limit test.",
    }


def test_write_rate_limit_returns_429(monkeypatch) -> None:
    monkeypatch.setenv("ND_RATE_LIMIT_MAX_WRITE_REQUESTS", "1")
    monkeypatch.setenv("ND_RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db_session() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    first = client.post("/api/v1/patients", json=_payload("PAT-6001"), headers={"X-Demo-Role": "admin"})
    assert first.status_code == 201

    second = client.post("/api/v1/patients", json=_payload("PAT-6002"), headers={"X-Demo-Role": "admin"})
    assert second.status_code == 429
    body = second.json()
    assert body["error"]["code"] == "rate_limit_exceeded"
    assert body["request_id"]

    app.dependency_overrides.clear()
    get_settings.cache_clear()
