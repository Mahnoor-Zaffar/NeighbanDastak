def test_healthcheck(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "NigehbaanDastak"
    assert body["database"] == "ok"
