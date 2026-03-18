from app.utils.conflict_rules import DOSAGE_LIMITS


def validate_dosage(drug, dosage):
    if drug not in DOSAGE_LIMITS:
        return None

    limits = DOSAGE_LIMITS[drug]

    if dosage < limits["min_mg"]:
        return f"Dosage too low (<{limits['min_mg']}mg)"

    if dosage > limits["max_mg"]:
        return f"Dosage too high (>{limits['max_mg']}mg)"

    return None