def test_health_check_ok(api_client) -> None:
    r = api_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body.get("timestamp"), str)

