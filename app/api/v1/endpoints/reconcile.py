from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone

from app.schemas.reconcile import ReconcileRequest
from app.schemas.resolve import ResolveRequest
from app.services.reconciliation_service import reconcile_medications
from app.dependencies.db import get_db
from app.db.repositories.reconciliation_repo import ReconciliationRepository
from app.db.repositories.patient_repo import PatientRepository

router = APIRouter()


# 🔹 POST: Run reconciliation
@router.post("/")
async def reconcile(payload: ReconcileRequest, db=Depends(get_db)):
    try:
        unified, conflicts = reconcile_medications(payload.sources)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 🔹 Convert Pydantic → dict
    sources_dict = [
        [med.model_dump() for med in source]
        for source in payload.sources
    ]

    # 🔹 Store reconciliation
    repo = ReconciliationRepository(db)
    rec_id = await repo.create(
        payload.patient_id,
        sources_dict,
        unified,
        conflicts
    )

    # 🔥 Update patient collection (FIXED INDENTATION)
    try:
        patient_repo = PatientRepository(db)
        await patient_repo.upsert_patient(payload.patient_id)
    except Exception:
        pass  # don't break reconciliation

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

    try:
        obj_id = ObjectId(reconciliation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid reconciliation ID")

    doc = await collection.find_one({"_id": obj_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    updated = False
    target_drug = None

    # 🔹 Step 1: Update conflict
    for conflict in doc.get("conflicts", []):
        if conflict.get("id") == conflict_id:

            conflict["status"] = "resolved"
            conflict["resolved_at"] = datetime.now(timezone.utc).isoformat()
            conflict["resolution_reason"] = payload.reason

            conflict["corrected_field"] = payload.field
            conflict["corrected_value"] = payload.corrected_value

            target_drug = conflict.get("drug")
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Conflict not found")

    # 🔥 Step 2: Update unified meds
    if target_drug:
        for med in doc.get("unified", []):
            if med.get("name") == target_drug:

                if payload.field == "dosage":
                    med["dosage"] = payload.corrected_value

                elif payload.field == "frequency":
                    med["frequency"] = payload.corrected_value

                elif payload.field == "name":
                    med["name"] = payload.corrected_value

                # 🔥 Optional: update stopped flag if needed
                if payload.field == "frequency":
                    if payload.corrected_value.lower() in ["stopped", "discontinued"]:
                        med["is_stopped"] = True
                    else:
                        med["is_stopped"] = False

    # 🔹 Step 3: Save
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
        "message": "Conflict resolved and unified meds updated",
        "updated_field": payload.field,
        "new_value": payload.corrected_value
    }