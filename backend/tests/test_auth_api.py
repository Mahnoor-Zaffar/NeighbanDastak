from __future__ import annotations

import pytest


AUTH_REQUIRED_CASES = [
    ("GET", "/api/v1/patients"),
    ("GET", "/api/v1/appointments"),
    ("GET", "/api/v1/visits/00000000-0000-0000-0000-000000000000"),
]


@pytest.mark.parametrize(("method", "path"), AUTH_REQUIRED_CASES)
def test_missing_role_header_returns_standard_401_shape(client, method: str, path: str) -> None:
    response = client.request(method, path)

    assert response.status_code == 401
    assert "X-Request-ID" in response.headers
    body = response.json()
    assert body["error"]["code"] == "http_401"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "X-Demo-Role" in body["error"]["message"]


def test_unsupported_role_returns_standard_403_shape(client, unsupported_role_headers) -> None:
    response = client.get("/api/v1/patients", headers=unsupported_role_headers)

    assert response.status_code == 403
    assert "X-Request-ID" in response.headers
    body = response.json()
    assert body["error"]["code"] == "http_403"
    assert body["error"]["message"] == "Unsupported role"
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_client_request_id_is_echoed_for_auth_errors(client) -> None:
    request_id = "auth-check-req-id"
    response = client.get("/api/v1/patients", headers={"X-Request-ID": request_id})

    assert response.status_code == 401
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id
