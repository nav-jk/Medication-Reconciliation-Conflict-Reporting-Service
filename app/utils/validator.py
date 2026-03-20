from app.utils.conflict_rules import DOSAGE_LIMITS


def validate_dosage(drug, dosage):
    if not drug or dosage is None:
        return None

    if drug not in DOSAGE_LIMITS:
        return None

    limits = DOSAGE_LIMITS[drug]

    if dosage < limits["min_mg"]:
        return {
            "type": "dosage_low",
            "message": f"{drug}: dosage too low (<{limits['min_mg']}mg)"
        }

    if dosage > limits["max_mg"]:
        return {
            "type": "dosage_high",
            "message": f"{drug}: dosage too high (>{limits['max_mg']}mg)"
        }

    return None