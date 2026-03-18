from fastapi import APIRouter, Depends
from app.schemas.medication import MedicationCreate
from app.dependencies.db import get_db
from app.db.repositories.medication_repo import MedicationRepository
from app.models.medication_model import medication_doc

router = APIRouter()


@router.post("/")
async def create_medication(payload: MedicationCreate, db=Depends(get_db)):
    repo = MedicationRepository(db)
    doc = medication_doc(payload.model_dump())
    med_id = await repo.create(doc)
    return {"id": med_id}


@router.get("/{patient_id}")
async def get_medications(patient_id: str, db=Depends(get_db)):
    repo = MedicationRepository(db)
    meds = await repo.get_by_patient(patient_id)
    return meds