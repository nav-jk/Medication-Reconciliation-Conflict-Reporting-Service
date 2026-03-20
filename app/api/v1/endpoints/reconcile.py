from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone

from app.schemas.reconcile import ReconcileRequest
from app.schemas.resolve import ResolveRequest
from app.services.reconciliation_service import reconcile_medications
from app.dependencies.db import get_db
from app.db.repositories.reconciliation_repo import ReconciliationRepository
from app.db.repositories.patient_repo import PatientRepository
from app.db.repositories.medication_repo import MedicationRepository
from app.schemas.medication import MedicationBase
import copy

router = APIRouter()


#  Helper: serialize anything → dict (Mongo-safe)
def serialize(data):
    if isinstance(data, list):
        return [serialize(x) for x in data]
    elif hasattr(data, "model_dump"):
        return data.model_dump()
    elif isinstance(data, dict):
        return {k: serialize(v) for k, v in data.items()}
    else:
        return data


@router.post("/")
async def reconcile(payload: ReconcileRequest, db=Depends(get_db)):
    print(" Incoming payload:", payload)

    medication_repo = MedicationRepository(db)

    if not payload.sources:
        print(" Fetching medications from DB")

        meds = await medication_repo.get_by_patient(payload.patient_id)

        if not meds:
            raise HTTPException(status_code=404, detail="No medications found")

        # group by source
        source_map = {}
        for m in meds:
            src = m.get("source")
            source_map.setdefault(src, []).append(m)

        # convert dict → Pydantic
        payload_sources = [
            [MedicationBase(**med) for med in meds]
            for meds in source_map.values()
        ]

    else:
        payload_sources = payload.sources  #  keep Pydantic


        for source in payload_sources:
            for med in source:
                await medication_repo.create({
                    **med.model_dump(),
                    "patient_id": payload.patient_id
                })

    try:
        unified, conflicts = reconcile_medications(payload_sources)
    except Exception as e:
        print(" Reconciliation failed:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    try:
        sources_dict = serialize(payload_sources)
        unified_dict = serialize(unified)
        conflicts_dict = serialize(conflicts)
    except Exception as e:
        print(" Serialization failed:", str(e))
        raise HTTPException(status_code=500, detail="Serialization error")

    try:
        repo = ReconciliationRepository(db)
        rec_id = await repo.create(
            payload.patient_id,
            sources_dict,
            unified,
            conflicts,
            payload.clinic_id  
        )
    except Exception as e:
        print(" DB insert failed:", str(e))
        raise HTTPException(status_code=500, detail="Database error")

    try:
        patient_repo = PatientRepository(db)
        await patient_repo.upsert_patient(payload.patient_id)
    except Exception as e:
        print(" Patient update failed:", str(e))

    return {
        "reconciliation_id": rec_id,
        "unified_medications": unified_dict,
        "conflicts": conflicts_dict
    }


#  GET: Patient reconciliation history
@router.get("/{patient_id}")
async def get_reconciliations(patient_id: str, db=Depends(get_db)):
    collection = db["reconciliations"]

    results = []

    async for doc in collection.find({"patient_id": patient_id}).sort("_id", -1):

        if not doc.get("versions"):
            continue  # skip malformed docs

        latest = doc["versions"][-1]

        results.append({
            "reconciliation_id": str(doc["_id"]),
            "patient_id": doc.get("patient_id"),
            "version": latest.get("version"),
            "timestamp": latest.get("timestamp"),
            "unified_medications": latest.get("unified", []),
            "conflicts": latest.get("conflicts", [])
        })

    return results


#  PATCH: Resolve conflict (VERSIONED — NO OVERWRITE)
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

    if not doc.get("versions"):
        raise HTTPException(status_code=500, detail="Invalid reconciliation structure")


    latest_version = doc.get("latest_version", 1)
    current_state = doc["versions"][-1]


    new_unified = copy.deepcopy(current_state.get("unified", []))
    new_conflicts = copy.deepcopy(current_state.get("conflicts", []))

    updated = False
    target_drug = None

   
    for conflict in new_conflicts:
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

 
    if target_drug:
        for med in new_unified:
            if med.get("name") == target_drug:

                if payload.field == "dosage":
                    med["dosage"] = payload.corrected_value

                elif payload.field == "frequency":
                    med["frequency"] = payload.corrected_value

                    val = payload.corrected_value.lower()
                    med["is_stopped"] = val in ["stopped", "discontinued"]

                elif payload.field == "name":
                    med["name"] = payload.corrected_value


    new_version = {
        "version": latest_version + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "unified": new_unified,
        "conflicts": new_conflicts,
        "action": "conflict_resolved",
        "meta": {
            "conflict_id": conflict_id,
            "reason": payload.reason,
            "field": payload.field,
            "corrected_value": payload.corrected_value
        }
    }

    try:
        await collection.update_one(
            {"_id": obj_id},
            {
                "$push": {"versions": new_version},
                "$set": {"latest_version": latest_version + 1}
            }
        )
    except Exception as e:
        print(" Update failed:", str(e))
        raise HTTPException(status_code=500, detail="Update failed")

    return {
        "message": "Conflict resolved (new version created)",
        "new_version": latest_version + 1,
        "updated_field": payload.field,
        "new_value": payload.corrected_value
    }