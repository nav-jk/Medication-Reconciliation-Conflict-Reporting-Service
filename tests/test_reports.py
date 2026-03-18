from fastapi.testclient import TestClient
from app.main import app


def test_conflict_report_basic(client):
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

    report = client.get("/api/v1/reports/conflicts")
    assert report.status_code == 200

