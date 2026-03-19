from datetime import datetime, timezone


class PatientRepository:

    def __init__(self, db):
        self.collection = db["patients"]

    async def upsert_patient(self, patient_id: str):
        now = datetime.now(timezone.utc).isoformat()

        await self.collection.update_one(
            {"patient_id": patient_id},
            {
                "$set": {"last_updated": now},
                "$setOnInsert": {
                    "patient_id": patient_id,
                    "created_at": now,
                    "total_reconciliations": 0
                },
                "$inc": {"total_reconciliations": 1}
            },
            upsert=True
        )