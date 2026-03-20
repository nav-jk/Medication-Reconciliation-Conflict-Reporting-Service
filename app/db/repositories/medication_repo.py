from bson import ObjectId

class MedicationRepository:
    def __init__(self, db):
        self.collection = db["medications"]

    def _serialize(self, doc):
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        return doc

    async def get_by_patient(self, patient_id: str):
        meds = await self.collection.find({"patient_id": patient_id}).to_list(100)
        return [self._serialize(m) for m in meds]

    async def create(self, doc):
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)  