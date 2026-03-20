from pydantic import BaseModel
from typing import List, Optional
from app.schemas.medication import MedicationBase


class ReconcileRequest(BaseModel):
    patient_id: str
    sources: List[List[MedicationBase]]
    clinic_id: Optional[str] = "default"    
