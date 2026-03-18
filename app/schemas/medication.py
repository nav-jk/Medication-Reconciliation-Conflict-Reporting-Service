from pydantic import BaseModel, Field
from typing import Optional


class MedicationBase(BaseModel):
    name: str
    dosage: Optional[str]
    frequency: Optional[str]
    source: str  # e.g., EMR / patient / discharge


class MedicationCreate(MedicationBase):
    patient_id: str


class MedicationOut(MedicationBase):
    id: str
    patient_id: str