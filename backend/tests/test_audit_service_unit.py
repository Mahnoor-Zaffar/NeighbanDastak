from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from app.db.models.audit_log import AuditLog
from app.services.audit_service import AuditContext, AuditService


def test_audit_service_sanitizes_metadata(db_session) -> None:
    service = AuditService(db_session)
    resource_id = uuid4()
    context = AuditContext(actor_role="admin", request_id="audit-unit-1", ip_address="127.0.0.1")

    service.log_action(
        context=context,
        action="patient.update",
        resource_type="patient",
        resource_id=resource_id,
        metadata={
            "long_text": "x" * 200,
            "number": 7,
            "nested_object": {"debug": True},
            "list_value": ["y" * 200, 1, {"data": "value"}] + list(range(30)),
        },
    )
    db_session.commit()

    log = db_session.scalar(select(AuditLog).where(AuditLog.resource_id == resource_id))
    assert log is not None
    assert log.metadata_json is not None
    assert log.metadata_json["long_text"] == "x" * 120
    assert log.metadata_json["number"] == 7
    assert isinstance(log.metadata_json["nested_object"], str)
    assert len(log.metadata_json["list_value"]) == 20
    assert log.metadata_json["list_value"][0] == "y" * 120


def test_audit_service_supports_none_metadata(db_session) -> None:
    service = AuditService(db_session)
    resource_id = uuid4()
    context = AuditContext(actor_role="doctor", request_id=None, ip_address=None)

    service.log_action(
        context=context,
        action="visit.create",
        resource_type="visit",
        resource_id=resource_id,
        metadata=None,
    )
    db_session.commit()

    log = db_session.scalar(select(AuditLog).where(AuditLog.resource_id == resource_id))
    assert log is not None
    assert log.metadata_json is None
