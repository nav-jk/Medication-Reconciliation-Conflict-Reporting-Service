from pydantic import BaseModel
from typing import List,Dict, Any
from app.schemas.medication import MedicationBase
from app.schemas.resolve import ResolveRequest


class ReconcileRequest(BaseModel):
    patient_id: str
    sources: List[List[MedicationBase]]  # multiple source lists


class Conflict(BaseModel):
    field: str
    values: List[str]


class ReconcileResponse(BaseModel):
    unified_medications: List[MedicationBase]
    conflicts: List[Conflict]

 
class ReconcileStore(BaseModel):
    patient_id: str
    sources: List[List[Dict[str, Any]]]
    unified: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]

class ResolveRequest(BaseModel):
    reason: str