from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta, timezone
from app.dependencies.db import get_db


router = APIRouter()

def serialize(doc):
    return doc

    
@router.get("/conflicts")
async def get_conflict_report(
    min_conflicts: int = Query(1, ge=1),
    days: int | None = Query(None, ge=1),
    db=Depends(get_db)
):
    collection = db["reconciliations"]

    pipeline = [
        {
            "$addFields": {
                "latest": {"$arrayElemAt": ["$versions", -1]}
            }
        },
        {
            "$unwind": "$latest.conflicts"
        },
        {
            "$match": {
                "latest.conflicts.status": "unresolved"
            }
        }
    ]

    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline.append({
            "$match": {
                "latest.timestamp": {"$gte": cutoff.isoformat()}
            }
        })

    pipeline.extend([
        {
            "$group": {
                "_id": "$patient_id",
                "conflict_count": {"$sum": 1}
            }
        },
        {
            "$match": {
                "conflict_count": {"$gte": min_conflicts}
            }
        },
        {
            "$project": {
                "_id": 0,
                "patient_id": "$_id",
                "conflict_count": 1
            }
        }
    ])

    results = []
    async for doc in collection.aggregate(pipeline):
        results.append(doc)

    return {
        "filters": {
            "min_conflicts": min_conflicts,
            "days": days
        },
        "results": results
    }


@router.get("/clinic/{clinic_id}/patients-with-conflicts")
async def patients_with_conflicts(clinic_id: str, db=Depends(get_db)):
    collection = db["reconciliations"]

    pipeline = [
        {"$match": {"clinic_id": clinic_id}},


        {
            "$addFields": {
                "latest": {"$arrayElemAt": ["$versions", -1]}
            }
        },

        {
            "$project": {
                "patient_id": 1,
                "unresolved_conflicts": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$latest.conflicts", []]},
                            "as": "c",
                            "cond": {"$ne": ["$$c.status", "resolved"]}
                        }
                    }
                }
            }
        },

        {"$match": {"unresolved_conflicts": {"$gte": 1}}},

        {
            "$group": {
                "_id": "$patient_id",
                "conflict_count": {"$sum": "$unresolved_conflicts"}
            }
        }
    ]

    results = []
    async for doc in collection.aggregate(pipeline):
        results.append({
            "patient_id": doc["_id"],
            "unresolved_conflicts": doc["conflict_count"]
        })

    return {"clinic_id": clinic_id, "results": results}

@router.get("/clinic/conflict-summary")
async def clinic_conflict_summary(
    days: int = Query(30),
    min_conflicts: int = Query(2),
    db=Depends(get_db)
):
    collection = db["reconciliations"]

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {
            "$addFields": {
                "latest": {"$arrayElemAt": ["$versions", -1]},
                "timestamp_dt": {
                    "$toDate": {
                        "$arrayElemAt": ["$versions.timestamp", -1]
                    }
                }
            }
        },
        {
            "$match": {
                "timestamp_dt": {"$gte": cutoff}
            }
        },
        {
            "$project": {
                "clinic_id": 1,
                "patient_id": 1,
                "conflict_count": {
                    "$size": {
                        "$ifNull": ["$latest.conflicts", []]
                    }
                }
            }
        },
        {
            "$match": {"conflict_count": {"$gte": min_conflicts}}
        },
        {
            "$group": {
                "_id": "$clinic_id",
                "patients": {"$addToSet": "$patient_id"},
                "total_cases": {"$sum": 1}
            }
        },
        {
            "$project": {
                "clinic_id": "$_id",
                "patient_count": {"$size": "$patients"},
                "total_cases": 1,
                "_id": 0
            }
        }
    ]

    results = []
    async for doc in collection.aggregate(pipeline):
        results.append(doc)

    return {"results": results}