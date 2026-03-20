from pydantic import BaseModel, field_validator
from typing import Optional
import re


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

        v = v.strip()

        # only alphabets + space (allow realistic names)
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Invalid medication name")

        if len(v) < 2:
            raise ValueError("Medication name too short")

        return v


    @field_validator("dosage")
    @classmethod
    def validate_dosage(cls, v):
        if v is None:
            return v

        v = str(v).lower().strip()

        # must match: 500mg, 1g, 0.5g
        match = re.match(r"^(\d*\.?\d+)\s*(mg|g)$", v)

        if not match:
            raise ValueError("Dosage must be like '500mg' or '1g'")

        value, unit = match.groups()
        value = float(value)

        # convert g → mg
        if unit == "g":
            value *= 1000


        if value <= 0 or value > 5000:
            raise ValueError("Dosage out of realistic bounds")

        return f"{int(value)}mg"


    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v is None:
            return v

        v = str(v).strip().lower()

        allowed_patterns = [
            r"^(od|bid|tid)$",
            r"^(once|twice|thrice) daily$",
            r"^\d-\d-\d$",              # 1-0-1
            r"^(stopped|discontinued)$",
            r"^(hs)$",                  # bedtime
            r"^(sos|prn)$",             # as needed
            r"^(once at night)$",
            r"^(after food)$"
        ]

        if not any(re.match(p, v) for p in allowed_patterns):
            raise ValueError(f"Invalid frequency: {v}")

        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        source_map = {
            "emr": "EMR",
            "patient": "Patient",
            "hospital": "Hospital",
            "discharge": "Hospital",
            "clinic_emr": "EMR",
            "patient_reported": "Patient"
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