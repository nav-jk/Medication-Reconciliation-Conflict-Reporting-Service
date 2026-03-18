from fastapi import APIRouter, Depends
from app.schemas.reconcile import ReconcileRequest
from app.services.reconciliation_service import reconcile_medications
from app.dependencies.db import get_db
from app.db.repositories.reconciliation_repo import ReconciliationRepository

router = APIRouter()


@router.post("/")
async def reconcile(payload: ReconcileRequest, db=Depends(get_db)):
    unified, conflicts = reconcile_medications(payload.sources)

    repo = ReconciliationRepository(db)
    sources_dict = [
    [med.model_dump() for med in source]
    for source in payload.sources
    ]

    rec_id = await repo.create(
        payload.patient_id,
        sources_dict,   # ✅ now JSON serializable
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
    data = await repo.get_by_patient(patient_id)
    return data