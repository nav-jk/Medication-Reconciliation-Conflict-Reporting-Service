from pydantic import BaseModel
from typing import List, Optional
from app.schemas.medication import MedicationBase


class ReconcileRequest(BaseModel):
    patient_id: str
    sources: Optional[List[List[MedicationBase]]] = None