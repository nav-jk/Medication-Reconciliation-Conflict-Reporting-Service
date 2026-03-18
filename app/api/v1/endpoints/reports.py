from fastapi import APIRouter, Depends
from app.dependencies.db import get_db

router = APIRouter()


@router.get("/conflicts")
async def patients_with_conflicts(db=Depends(get_db)):
    collection = db["reconciliations"]

    pipeline = [
        {"$unwind": "$conflicts"},
        {"$match": {"conflicts.status": "unresolved"}},
        {
            "$group": {
                "_id": "$patient_id",
                "conflict_count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "patient_id": "$_id",
                "conflict_count": 1,
                "_id": 0
            }
        }
    ]

    results = []
    async for doc in collection.aggregate(pipeline):
        results.append(doc)

    return results