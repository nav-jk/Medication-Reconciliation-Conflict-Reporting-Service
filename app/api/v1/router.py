from fastapi import APIRouter
from app.api.v1.endpoints import reconcile, medications, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(medications.router, prefix="/medications", tags=["Medications"])
api_router.include_router(reconcile.router, prefix="/reconcile", tags=["Reconciliation"])