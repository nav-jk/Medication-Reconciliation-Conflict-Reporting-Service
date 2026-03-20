from datetime import datetime, timezone


class PatientRepository:

    def __init__(self, db):
        self.collection = db["patients"]

    async def upsert_patient(self, patient_id: str):
        now = datetime.now(timezone.utc).isoformat()

        # Check if patient exists
        existing = await self.collection.find_one({"patient_id": patient_id})

        if existing:
            #  Update existing patient
            result = await self.collection.update_one(
                {"patient_id": patient_id},
                {
                    "$set": {"last_updated": now},
                    "$inc": {"total_reconciliations": 1}
                }
            )
        else:
  
            result = await self.collection.insert_one({
                "patient_id": patient_id,
                "created_at": now,
                "last_updated": now,
                "total_reconciliations": 1
            })

        print(" Patient write result:", result)