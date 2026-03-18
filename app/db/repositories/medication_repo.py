from bson import ObjectId


class MedicationRepository:

    def __init__(self, db):
        self.collection = db["medications"]

    async def create(self, data: dict):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_patient(self, patient_id: str):
        meds = []
        async for doc in self.collection.find({"patient_id": patient_id}):
            doc["id"] = str(doc["_id"])
            meds.append(doc)
        return meds