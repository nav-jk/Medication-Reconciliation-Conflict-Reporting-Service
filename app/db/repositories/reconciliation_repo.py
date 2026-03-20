from datetime import datetime, timezone


class ReconciliationRepository:
    def __init__(self, db):
        self.collection = db["reconciliations"]

    async def create(self, patient_id, sources, unified, conflicts, clinic_id = "default"):
        existing = await self.collection.find_one({"patient_id": patient_id})

        if not existing:
            # First version
            doc = {
                "patient_id": patient_id,
                "clinic_id": clinic_id,
                "sources": sources,
                "latest_version": 1,
                "versions": [
                    {
                        "version": 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "unified": unified,
                        "conflicts": conflicts,
                        "action": "created"
                    }
                ]
            }
            result = await self.collection.insert_one(doc)
            return str(result.inserted_id)

        else:
            # Increment version
            new_version = existing["latest_version"] + 1

            new_entry = {
                "version": new_version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "unified": unified,
                "conflicts": conflicts,
                "action": "updated"
            }

            await self.collection.update_one(
                {"patient_id": patient_id},
                {
                    "$set": {
                        "latest_version": new_version,
                        "sources": sources,
                        "clinic_id":clinic_id
                    },
                    "$push": {
                        "versions": new_entry
                    }
                }
            )

            return str(existing["_id"])

    async def get_by_patient(self, patient_id):
        results = []

        async for doc in self.collection.find(
            {"patient_id": patient_id}
        ).sort("_id", -1):

            # 🔥 skip bad docs
            if not doc.get("versions"):
                continue

            latest = doc["versions"][-1]

            rec = {
                "reconciliation_id": str(doc["_id"]),
                "patient_id": doc.get("patient_id"),

                "version": latest.get("version"),
                "timestamp": latest.get("timestamp"),

                "unified_medications": latest.get("unified", []),
                "conflicts": latest.get("conflicts", []),
                "history": doc.get("versions", [])
            }

            # 🔹 normalize timestamp (safety)
            if isinstance(rec["timestamp"], datetime):
                rec["timestamp"] = rec["timestamp"].isoformat()

            results.append(rec)

        return results