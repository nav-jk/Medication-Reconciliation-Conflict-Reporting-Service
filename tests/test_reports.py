from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_conflict_report_basic():
    # First create data
    payload = {
        "patient_id": "ptest",
        "sources": [
            [
                {"name": "Paracetamol", "dosage": "500mg", "frequency": "BID", "source": "EMR"}
            ],
            [
                {"name": "Paracetamol", "dosage": "650mg", "frequency": "OD", "source": "Patient"}
            ]
        ]
    }

    res = client.post("/api/v1/reconcile/", json=payload)
    assert res.status_code == 200

    # Call report
    report = client.get("/api/v1/reports/conflicts")
    assert report.status_code == 200

    data = report.json()

    assert "results" in data
    assert isinstance(data["results"], list)


def test_conflict_report_filters():
    res = client.get("/api/v1/reports/conflicts?min_conflicts=1&days=30")
    assert res.status_code == 200

    data = res.json()

    assert data["filters"]["min_conflicts"] == 1
    assert data["filters"]["days"] == 30