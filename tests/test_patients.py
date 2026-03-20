def test_invalid_limit(client):
    res = client.get("/api/v1/patients/?limit=1000")
    assert res.status_code == 422


def test_negative_skip(client):
    res = client.get("/api/v1/patients/?skip=-1")
    assert res.status_code == 422
