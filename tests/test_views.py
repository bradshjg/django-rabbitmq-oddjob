def test_result_view(client):
    resp = client.get("/oddjob/result/testtoken123/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result_token"] == "testtoken123"
    assert data["status"] == "success"
    assert data["data"] == "This is a dummy response."
