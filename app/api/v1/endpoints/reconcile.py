from fastapi import APIRouter, Depends, HTTPException
from app.schemas.reconcile import ReconcileRequest
from app.services.reconciliation_service import reconcile_medications
from app.dependencies.db import get_db
from app.db.repositories.reconciliation_repo import ReconciliationRepository

from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel

router = APIRouter()


# 🔹 Resolve request schema
class ResolveRequest(BaseModel):
    reason: str


@router.post("/")
async def reconcile(payload: ReconcileRequest, db=Depends(get_db)):
    unified, conflicts = reconcile_medications(payload.sources)

    # 🔥 Convert Pydantic → dict
    sources_dict = [
        [med.model_dump() for med in source]
        for source in payload.sources
    ]

    repo = ReconciliationRepository(db)

    rec_id = await repo.create(
        payload.patient_id,
        sources_dict,
        unified,
        conflicts
    )

    return {
        "reconciliation_id": rec_id,
        "unified_medications": unified,
        "conflicts": conflicts
    }


@router.get("/{patient_id}")
async def get_reconciliations(patient_id: str, db=Depends(get_db)):
    repo = ReconciliationRepository(db)
    return await repo.get_by_patient(patient_id)


# 🔥 FIXED RESOLVE ENDPOINT (only one)
@router.patch("/resolve/{reconciliation_id}/{conflict_id}")
async def resolve_conflict(
    reconciliation_id: str,
    conflict_id: str,
    payload: ResolveRequest,
    db=Depends(get_db)
):
    collection = db["reconciliations"]

    doc = await collection.find_one({"_id": ObjectId(reconciliation_id)})

    if not doc:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    updated = False

    for conflict in doc["conflicts"]:
        if conflict.get("id") == conflict_id:
            conflict["status"] = "resolved"
            conflict["resolved_at"] = datetime.now(timezone.utc).isoformat()
            conflict["resolution_reason"] = payload.reason
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Conflict not found")

    await collection.update_one(
        {"_id": ObjectId(reconciliation_id)},
        {"$set": {"conflicts": doc["conflicts"]}}
    )

    return {"message": "Conflict resolved"}