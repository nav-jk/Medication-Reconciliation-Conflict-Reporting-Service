from pydantic import BaseModel
from typing import Literal


class ResolveRequest(BaseModel):
    reason: str
    field: Literal["name", "dosage", "frequency"]
    corrected_value: str