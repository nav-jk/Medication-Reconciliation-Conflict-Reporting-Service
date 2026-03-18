from app.utils.normalizer import (
    normalize_name,
    normalize_dosage,
    normalize_frequency,
    extract_dosage_value
)
from app.utils.validator import validate_dosage


def reconcile_medications(sources):
    med_map = {}
    conflicts = []

    for source in sources:
        for med in source:
            norm_name = normalize_name(med.name)
            norm_dosage = normalize_dosage(med.dosage)
            norm_freq = normalize_frequency(med.frequency)

            dosage_val = extract_dosage_value(norm_dosage)

            # 🔹 Run validation for EVERY entry
            if dosage_val:
                validation_issue = validate_dosage(norm_name, dosage_val)
                if validation_issue:
                    conflicts.append({
                        "drug": norm_name,
                        "type": "UNCOMMON_DOSAGE",
                        "details": validation_issue,
                        "source": med.source
                    })

            # 🔹 First occurrence
            if norm_name not in med_map:
                med_map[norm_name] = {
                    "name": norm_name,
                    "dosage": norm_dosage,
                    "frequency": norm_freq,
                    "sources": [med.source]
                }
                continue

            existing = med_map[norm_name]

            # 🔹 Deduplicate sources
            if med.source not in existing["sources"]:
                existing["sources"].append(med.source)

            # 🔹 DOSAGE conflict
            if norm_dosage and existing["dosage"] and norm_dosage != existing["dosage"]:
                conflicts.append({
                    "drug": norm_name,
                    "type": "DOSAGE_MISMATCH",
                    "values": [existing["dosage"], norm_dosage],
                    "sources": existing["sources"]
                })

            # 🔹 FREQUENCY conflict
            if norm_freq and existing["frequency"] and norm_freq != existing["frequency"]:
                conflicts.append({
                    "drug": norm_name,
                    "type": "FREQUENCY_MISMATCH",
                    "values": [existing["frequency"], norm_freq],
                    "sources": existing["sources"]
                })

            # 🔹 Smart update (prefer non-null / latest info)
            if not existing["dosage"] and norm_dosage:
                existing["dosage"] = norm_dosage

            if not existing["frequency"] and norm_freq:
                existing["frequency"] = norm_freq

    unified = list(med_map.values())

    return unified, conflicts