from pydantic import BaseModel, field_validator
from typing import Optional


class MedicationBase(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    source: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Medication name cannot be empty")
        return v.strip()

    @field_validator("dosage")
    @classmethod
    def validate_dosage(cls, v):
        if v is None:
            return v
        v = str(v).lower().strip()

        # allow only patterns like "500mg"
        if not any(char.isdigit() for char in v):
            raise ValueError("Invalid dosage format")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v is None:
            return v
        return str(v).strip().lower()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        source_map = {
            "emr": "EMR",
            "patient": "Patient",
            "hospital": "Hospital",
            "discharge": "Hospital",
            "clinic_emr" : "EMR",
            "patient_reported" : "Patient"
        }

        v_clean = v.strip().lower()

        if v_clean not in source_map:
            raise ValueError(f"Invalid source: {v}")

        return source_map[v_clean]


class MedicationCreate(MedicationBase):
    patient_id: str


class MedicationOut(MedicationBase):
    id: str
    patient_id: str