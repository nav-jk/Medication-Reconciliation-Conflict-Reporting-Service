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

router = APIRouter()


# 🔥 Helper: serialize anything → dict (Mongo-safe)
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
    print("📥 Incoming payload:", payload)

    medication_repo = MedicationRepository(db)

    # 🔥 STEP 0: Get sources
    if not payload.sources:
        print("📦 Fetching medications from DB")

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
        payload_sources = payload.sources  # ✅ keep Pydantic

        # 🔥 also store meds in DB (history)
        for source in payload_sources:
            for med in source:
                await medication_repo.create({
                    **med.model_dump(),
                    "patient_id": payload.patient_id
                })

    # 🔥 STEP 1: Reconcile (Pydantic objects)
    try:
        unified, conflicts = reconcile_medications(payload_sources)
    except Exception as e:
        print("❌ Reconciliation failed:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    # 🔥 STEP 2: Convert everything to dict (VERY IMPORTANT)
    try:
        sources_dict = serialize(payload_sources)
        unified_dict = serialize(unified)
        conflicts_dict = serialize(conflicts)
    except Exception as e:
        print("❌ Serialization failed:", str(e))
        raise HTTPException(status_code=500, detail="Serialization error")

    # 🔥 STEP 3: Store in DB
    try:
        repo = ReconciliationRepository(db)
        rec_id = await repo.create(
            payload.patient_id,
            sources_dict,
            unified_dict,
            conflicts_dict
        )
    except Exception as e:
        print("❌ DB insert failed:", str(e))
        raise HTTPException(status_code=500, detail="Database error")

    # 🔥 STEP 4: Update patient (non-blocking)
    try:
        patient_repo = PatientRepository(db)
        await patient_repo.upsert_patient(payload.patient_id)
    except Exception as e:
        print("❌ Patient update failed:", str(e))

    return {
        "reconciliation_id": rec_id,
        "unified_medications": unified_dict,
        "conflicts": conflicts_dict
    }