from datetime import datetime, timezone


class ReconciliationRepository:
    def __init__(self, db):
        self.collection = db["reconciliations"]

    async def create(self, patient_id, sources, unified, conflicts):
        doc = {
            "patient_id": patient_id,
            "timestamp": datetime.now(timezone.utc),
            "sources": sources,
            "unified": unified,
            "conflicts": conflicts
        }

        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)


    async def get_by_patient(self, patient_id):
        results = []

        async for doc in self.collection.find({"patient_id": patient_id}):

            doc["id"] = str(doc["_id"])
            doc.pop("_id", None)

            if "timestamp" in doc and isinstance(doc["timestamp"], datetime):
                doc["timestamp"] = doc["timestamp"].isoformat()

            results.append(doc)

        return results