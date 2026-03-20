from datetime import datetime, timezone


class ReconciliationRepository:
    def __init__(self, db):
        self.collection = db["reconciliations"]

    async def create(self, patient_id, sources, unified, conflicts):
        doc = {
            "patient_id": patient_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": sources,
            "unified": unified,
            "conflicts": conflicts
        }

        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)


    async def get_by_patient(self, patient_id):
        results = []

        async for doc in self.collection.find({"patient_id": patient_id}).sort("timestamp", -1):

            rec = {
                "reconciliation_id": str(doc["_id"]),
                "patient_id": doc.get("patient_id"),
                "timestamp": doc.get("timestamp"),

                "sources": doc.get("sources", []),

                "unified_medications": doc.get("unified", []),

                "conflicts": []
            }

            #  Normalize timestamp
            if isinstance(rec["timestamp"], datetime):
                rec["timestamp"] = rec["timestamp"].isoformat()

            #  Process conflicts
            for c in doc.get("conflicts", []):
                rec["conflicts"].append({
                    "id": c.get("id"),
                    "drug": c.get("drug"),
                    "type": c.get("type"),
                    "severity": c.get("severity"),
                    "status": c.get("status"),

                    "values": c.get("values"),
                    "sources": c.get("sources"),
                    "reason": c.get("reason"),

                    "resolved_at": c.get("resolved_at"),
                    "resolution_reason": c.get("resolution_reason"),
                    "corrected_field": c.get("corrected_field"),
                    "corrected_value": c.get("corrected_value"),
                })

            results.append(rec)

        return results