def test_create_medication_missing_fields(client):
    res = client.post("/api/v1/medications/", json={
        "name": "Paracetamol"
    })
    assert res.status_code == 422


def test_create_medication_invalid_type(client):
    res = client.post("/api/v1/medications/", json={
        "name": 123,
        "dosage": "500mg",
        "frequency": "BID",
        "source": "EMR",
        "patient_id": "p1"
    })
    assert res.status_code == 422


def test_reconcile_empty_sources(client):
    res = client.post("/api/v1/reconcile/", json={
        "patient_id": "p1",
        "sources": []
    })
    assert res.status_code == 200  # or 422 depending on your design


def test_reconcile_missing_patient_id(client):
    res = client.post("/api/v1/reconcile/", json={
        "sources": []
    })
    assert res.status_code == 422