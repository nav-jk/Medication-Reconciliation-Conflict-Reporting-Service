from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies.db import get_db

router = APIRouter()


#  Helper: serialize Mongo doc
def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc


#  GET: List all patients (with pagination)
@router.get("/")
async def list_patients(
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("last_updated"),  # or created_at
    db=Depends(get_db)
):
    collection = db["patients"]

    cursor = collection.find().sort(sort_by, -1).skip(skip).limit(limit)

    patients = []
    async for doc in cursor:
        patients.append(serialize(doc))

    return {
        "count": len(patients),
        "results": patients
    }


#  GET: Single patient
@router.get("/{patient_id}")
async def get_patient(patient_id: str, db=Depends(get_db)):
    collection = db["patients"]

    doc = await collection.find_one({"patient_id": patient_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Patient not found")

    return serialize(doc)


# #  GET: Patient stats (aggregated)
# @router.get("/{patient_id}/stats")
# async def get_patient_stats(patient_id: str, db=Depends(get_db)):
#     rec_collection = db["reconciliations"]

#     pipeline = [
#         {"$match": {"patient_id": patient_id}},
#         {
#             "$project": {
#                 "conflict_count": {"$size": {"$ifNull": ["$conflicts", []]}}
#             }
#         },
#         {
#             "$group": {
#                 "_id": "$patient_id",
#                 "total_reconciliations": {"$sum": 1},
#                 "total_conflicts": {"$sum": "$conflict_count"},
#                 "avg_conflicts": {"$avg": "$conflict_count"}
#             }
#         }
#     ]

#     results = []
#     async for doc in rec_collection.aggregate(pipeline):
#         results.append(doc)

#     if not results:
#         raise HTTPException(status_code=404, detail="No data for patient")

#     stats = results[0]
#     stats["_id"] = str(stats["_id"]) if "_id" in stats else None

#     return stats

@router.get("/{patient_id}/timeline")
async def get_patient_timeline(patient_id: str, db=Depends(get_db)):
    collection = db["reconciliations"]

    doc = await collection.find_one({"patient_id": patient_id})

    if not doc:
        raise HTTPException(status_code=404, detail="No history found")

    versions = doc.get("versions", [])

    if not versions:
        return {"patient_id": patient_id, "timeline": []}

    versions = sorted(versions, key=lambda x: x.get("version", 0))

    timeline = []
    prev = None

    for v in versions:
        current_meds = {m["name"]: m for m in v.get("unified", [])}
        prev_meds = {m["name"]: m for m in prev.get("unified", [])} if prev else {}

        changes = []

        #  ADDED
        for name in current_meds:
            if name not in prev_meds:
                changes.append({
                    "type": "ADDED",
                    "drug": name,
                    "data": current_meds[name]
                })

        #  REMOVED
        for name in prev_meds:
            if name not in current_meds:
                changes.append({
                    "type": "REMOVED",
                    "drug": name,
                    "data": prev_meds[name]
                })

        #  MODIFIED
        for name in current_meds:
            if name in prev_meds:
                curr = current_meds[name]
                prev_val = prev_meds[name]

                for field in ["dosage", "frequency", "is_stopped"]:
                    if curr.get(field) != prev_val.get(field):
                        changes.append({
                            "type": "MODIFIED",
                            "drug": name,
                            "field": field,
                            "old": prev_val.get(field),
                            "new": curr.get(field)
                        })

        #  CORRECTIONS (resolved conflicts)
        corrections = [
            {
                "drug": c.get("drug"),
                "field": c.get("corrected_field"),
                "value": c.get("corrected_value"),
                "resolved_at": c.get("resolved_at"),
                "reason": c.get("resolution_reason")
            }
            for c in v.get("conflicts", [])
            if c.get("status") == "resolved"
        ]

        timeline.append({
            "version": v.get("version"),
            "timestamp": v.get("timestamp"),
            "reconciliation_id": str(doc["_id"]),
            "medications": v.get("unified", []),
            "changes": changes,
            "corrections": corrections
        })

        prev = v

    return {
        "patient_id": patient_id,
        "timeline": timeline
    }