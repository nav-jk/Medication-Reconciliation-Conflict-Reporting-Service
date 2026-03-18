from pydantic import BaseModel
from typing import List
from app.schemas.medication import MedicationBase


class ReconcileRequest(BaseModel):
    patient_id: str
    sources: List[List[MedicationBase]]  # multiple source lists


class Conflict(BaseModel):
    field: str
    values: List[str]


class ReconcileResponse(BaseModel):
    unified_medications: List[MedicationBase]
    conflicts: List[Conflict]