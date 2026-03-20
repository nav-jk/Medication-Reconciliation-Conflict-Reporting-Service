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

    cursor = collection.find(
        {"patient_id": patient_id}
    ).sort("timestamp", 1)  # ascending (timeline)

    history = []

    async for doc in cursor:
        history.append({
            "timestamp": doc.get("timestamp"),
            "reconciliation_id": str(doc["_id"]),
            "unified": doc.get("unified", []),
            "conflicts": doc.get("conflicts", [])
        })

    if not history:
        raise HTTPException(status_code=404, detail="No history found")

    # 🔥 Build timeline with changes
    timeline = []

    prev = None

    for snap in history:
        changes = []

        current_meds = {m["name"]: m for m in snap["unified"]}
        prev_meds = {m["name"]: m for m in prev["unified"]} if prev else {}

        # 🔹 Detect NEW meds
        for name in current_meds:
            if name not in prev_meds:
                changes.append({
                    "type": "ADDED",
                    "drug": name,
                    "data": current_meds[name]
                })

        # 🔹 Detect REMOVED meds
        for name in prev_meds:
            if name not in current_meds:
                changes.append({
                    "type": "REMOVED",
                    "drug": name,
                    "data": prev_meds[name]
                })

        # 🔹 Detect MODIFIED meds
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

        # 🔹 Include corrections from conflicts
        corrections = [
            {
                "drug": c.get("drug"),
                "field": c.get("corrected_field"),
                "value": c.get("corrected_value"),
                "resolved_at": c.get("resolved_at"),
                "reason": c.get("resolution_reason")
            }
            for c in snap.get("conflicts", [])
            if c.get("status") == "resolved"
        ]

        timeline.append({
            "timestamp": snap["timestamp"],
            "reconciliation_id": snap["reconciliation_id"],
            "medications": snap["unified"],
            "changes": changes,
            "corrections": corrections
        })

        prev = snap

    return {
        "patient_id": patient_id,
        "timeline": timeline
    }