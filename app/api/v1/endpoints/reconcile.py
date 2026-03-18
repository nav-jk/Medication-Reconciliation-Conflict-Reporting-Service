from fastapi import APIRouter
from app.schemas.reconcile import ReconcileRequest
from app.services.reconciliation_service import reconcile_medications

router = APIRouter()


@router.post("/")
async def reconcile(payload: ReconcileRequest):
    unified, conflicts = reconcile_medications(payload.sources)

    return {
        "unified_medications": unified,
        "conflicts": conflicts
    }