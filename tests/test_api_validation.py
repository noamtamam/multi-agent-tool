def test_create_task_rejects_empty_task(api_client) -> None:
    r = api_client.post("/tasks", json={"task": ""})
    assert r.status_code == 422

