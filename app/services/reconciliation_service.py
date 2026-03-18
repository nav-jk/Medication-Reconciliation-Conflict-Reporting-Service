from collections import defaultdict


def reconcile_medications(sources):
    merged = {}
    conflicts = []

    for source in sources:
        for med in source:
            key = med.name.lower()

            if key not in merged:
                merged[key] = med
            else:
                existing = merged[key]

                if med.dosage != existing.dosage:
                    conflicts.append({
                        "field": "dosage",
                        "values": [existing.dosage, med.dosage]
                    })

    return list(merged.values()), conflicts