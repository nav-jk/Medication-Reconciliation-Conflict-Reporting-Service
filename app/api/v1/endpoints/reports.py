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