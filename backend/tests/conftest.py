from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rbac import Role
from app.db.models.user import User
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-Demo-Role": "admin"}


@pytest.fixture
def doctor_headers() -> dict[str, str]:
    return {"X-Demo-Role": "doctor"}


@pytest.fixture
def unsupported_role_headers() -> dict[str, str]:
    return {"X-Demo-Role": "guest"}


@pytest.fixture
def receptionist_headers() -> dict[str, str]:
    return {"X-Demo-Role": "receptionist"}


@pytest.fixture
def patient_payload_factory() -> Callable[..., dict[str, Any]]:
    def _build(record_number: str = "PAT-9001", **overrides: Any) -> dict[str, Any]:
        payload = {
            "record_number": record_number,
            "first_name": "Amina",
            "last_name": "Khan",
            "date_of_birth": "1993-04-18",
            "email": f"{record_number.lower()}@example.com",
            "phone": "+1 555 0101",
            "city": "Karachi",
            "notes": "Demo patient record.",
        }
        payload.update(overrides)
        return payload

    return _build


@pytest.fixture
def appointment_payload_factory() -> Callable[..., dict[str, Any]]:
    def _build(patient_id: str, **overrides: Any) -> dict[str, Any]:
        payload = {
            "patient_id": patient_id,
            "scheduled_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "reason": "Routine follow-up",
            "notes": "Bring latest lab reports.",
        }
        payload.update(overrides)
        return payload

    return _build


@pytest.fixture
def visit_payload_factory() -> Callable[..., dict[str, Any]]:
    def _build(patient_id: str, **overrides: Any) -> dict[str, Any]:
        payload = {
            "patient_id": patient_id,
            "appointment_id": None,
            "started_at": datetime.now(UTC).isoformat(),
            "ended_at": None,
            "complaint": "Mild fever",
            "diagnosis_summary": "Viral syndrome",
            "notes": "Hydration and rest advised.",
        }
        payload.update(overrides)
        return payload

    return _build


@pytest.fixture
def create_patient(
    client: TestClient,
    admin_headers: dict[str, str],
    patient_payload_factory: Callable[..., dict[str, Any]],
) -> Callable[..., Any]:
    def _create(
        *,
        record_number: str = "PAT-9001",
        headers: dict[str, str] | None = None,
        **overrides: Any,
    ):
        payload = patient_payload_factory(record_number=record_number, **overrides)
        return client.post("/api/v1/patients", json=payload, headers=headers or admin_headers)

    return _create


@pytest.fixture
def create_appointment(
    client: TestClient,
    doctor_headers: dict[str, str],
    appointment_payload_factory: Callable[..., dict[str, Any]],
) -> Callable[..., Any]:
    def _create(
        *,
        patient_id: str,
        headers: dict[str, str] | None = None,
        **overrides: Any,
    ):
        payload = appointment_payload_factory(patient_id, **overrides)
        return client.post("/api/v1/appointments", json=payload, headers=headers or doctor_headers)

    return _create


@pytest.fixture
def create_visit(
    client: TestClient,
    doctor_headers: dict[str, str],
    visit_payload_factory: Callable[..., dict[str, Any]],
) -> Callable[..., Any]:
    def _create(
        *,
        patient_id: str,
        headers: dict[str, str] | None = None,
        **overrides: Any,
    ):
        payload = visit_payload_factory(patient_id, **overrides)
        return client.post("/api/v1/visits", json=payload, headers=headers or doctor_headers)

    return _create


@pytest.fixture
def create_user(db_session: Session) -> Callable[..., User]:
    def _create(
        *,
        email: str,
        full_name: str,
        role: Role,
        password_hash: str = "test-password-hash",
        is_active: bool = True,
        specialty: str | None = None,
        license_number: str | None = None,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            password_hash=password_hash,
            is_active=is_active,
            specialty=specialty,
            license_number=license_number,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create


@pytest.fixture
def seed_clinic_data(
    create_patient: Callable[..., Any],
    create_appointment: Callable[..., Any],
    create_visit: Callable[..., Any],
):
    patient_one_response = create_patient(record_number="PAT-SEED-001")
    patient_two_response = create_patient(
        record_number="PAT-SEED-002",
        first_name="Bilal",
        last_name="Ahmed",
        city="Lahore",
    )
    assert patient_one_response.status_code == 201
    assert patient_two_response.status_code == 201
    patient_one = patient_one_response.json()
    patient_two = patient_two_response.json()

    appointment_response = create_appointment(patient_id=patient_one["id"])
    assert appointment_response.status_code == 201
    appointment = appointment_response.json()

    visit_response = create_visit(
        patient_id=patient_one["id"],
        appointment_id=appointment["id"],
    )
    assert visit_response.status_code == 201
    visit = visit_response.json()

    return {
        "patients": [patient_one, patient_two],
        "appointment": appointment,
        "visit": visit,
    }
