from datetime import datetime, timezone


def medication_doc(data: dict):
    return {
        "name": data["name"],
        "dosage": data.get("dosage"),
        "frequency": data.get("frequency"),
        "source": data["source"],
        "patient_id": data["patient_id"],
        "created_at": datetime.now(timezone.utc)
    }