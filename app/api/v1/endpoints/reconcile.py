from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone

from app.schemas.reconcile import ReconcileRequest
from app.schemas.resolve import ResolveRequest
from app.services.reconciliation_service import reconcile_medications
from app.dependencies.db import get_db
from app.db.repositories.reconciliation_repo import ReconciliationRepository

router = APIRouter()


# 🔹 POST: Run reconciliation
@router.post("/")
async def reconcile(payload: ReconcileRequest, db=Depends(get_db)):
    try:
        unified, conflicts = reconcile_medications(payload.sources)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert Pydantic → dict
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


# 🔹 GET: Patient reconciliation history
@router.get("/{patient_id}")
async def get_reconciliations(patient_id: str, db=Depends(get_db)):
    repo = ReconciliationRepository(db)
    return await repo.get_by_patient(patient_id)


# 🔹 PATCH: Resolve conflict
@router.patch("/resolve/{reconciliation_id}/{conflict_id}")
async def resolve_conflict(
    reconciliation_id: str,
    conflict_id: str,
    payload: ResolveRequest,
    db=Depends(get_db)
):
    collection = db["reconciliations"]

    # 🔥 Validate ObjectId
    try:
        obj_id = ObjectId(reconciliation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid reconciliation ID")

    doc = await collection.find_one({"_id": obj_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    updated = False

    for conflict in doc.get("conflicts", []):
        if conflict.get("id") == conflict_id:

            # ✅ mark resolved
            conflict["status"] = "resolved"
            conflict["resolved_at"] = datetime.now(timezone.utc).isoformat()
            conflict["resolution_reason"] = payload.reason

            # 🔥 store correction
            conflict["corrected_field"] = payload.field
            conflict["corrected_value"] = payload.corrected_value

            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Conflict not found")

    # 🔥 OPTIONAL (VERY GOOD): update unified meds
    for med in doc.get("unified", []):
        if med.get("name") == conflict.get("drug"):
            if payload.field == "dosage":
                med["dosage"] = payload.corrected_value
            elif payload.field == "frequency":
                med["frequency"] = payload.corrected_value
            elif payload.field == "name":
                med["name"] = payload.corrected_value

    # 🔥 save back
    await collection.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "conflicts": doc["conflicts"],
                "unified": doc["unified"]
            }
        }
    )

    return {
        "message": "Conflict resolved successfully",
        "conflict_id": conflict_id,
        "updated_field": payload.field,
        "new_value": payload.corrected_value
    }