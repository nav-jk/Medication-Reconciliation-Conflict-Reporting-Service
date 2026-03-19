from fastapi import APIRouter
from app.api.v1.endpoints import reconcile, medications, health, reports, patients


api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(medications.router, prefix="/medications", tags=["Medications"])
api_router.include_router(reconcile.router, prefix="/reconcile", tags=["Reconciliation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])