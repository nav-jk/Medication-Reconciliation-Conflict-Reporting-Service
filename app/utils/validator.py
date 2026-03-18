from app.utils.drug_db import DRUG_DB


def validate_dosage(drug_name: str, dosage_mg: int):
    if drug_name not in DRUG_DB:
        return None  # unknown drug, skip validation

    allowed = DRUG_DB[drug_name].get("common_strengths_mg", [])

    if dosage_mg not in allowed:
        return {
            "type": "UNCOMMON_DOSAGE",
            "message": f"{dosage_mg}mg is not a common strength",
            "expected": allowed
        }

    return None 