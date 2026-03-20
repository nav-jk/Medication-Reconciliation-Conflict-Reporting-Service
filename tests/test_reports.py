from fastapi.testclient import TestClient
from app.main import app



def test_conflict_report_invalid_query(client):
    res = client.get("/api/v1/reports/conflicts?min_conflicts=-1")
    assert res.status_code == 422

