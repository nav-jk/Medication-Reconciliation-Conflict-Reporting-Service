from app.utils.normalizer import (
    normalize_name,
    normalize_dosage,
    normalize_frequency,
    extract_dosage_value
)
from app.utils.validator import validate_dosage
from app.utils.constants import SEVERITY, SOURCE_PRIORITY


def reconcile_medications(sources):
    med_map = {}
    conflicts = []
    conflict_set = set()
    source_drug_map = {}
    seen_entries = set()  # ✅ FIX: moved inside

    # 🔹 Step 1: Track drugs per source
    for source in sources:
        for med in source:
            norm_name = normalize_name(med.name)
            source_drug_map.setdefault(med.source, set()).add(norm_name)

    # 🔹 Step 2: Process medications
    for source in sources:
        for med in source:
            norm_name = normalize_name(med.name)
            norm_dosage = normalize_dosage(med.dosage)
            norm_freq = normalize_frequency(med.frequency)

            # 🔥 DUPLICATE DETECTION (FIRST THING)
            entry_key = (med.source, norm_name, norm_dosage, norm_freq)

            if entry_key in seen_entries:
                key = (norm_name, "DUPLICATE_ENTRY", med.source)
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        "drug": norm_name,
                        "type": "DUPLICATE_ENTRY",
                        "severity": "LOW",
                        "source": med.source
                    })
                continue

            seen_entries.add(entry_key)

            dosage_val = extract_dosage_value(norm_dosage)

            # 🔹 Validation
            if dosage_val:
                validation_issue = validate_dosage(norm_name, dosage_val)
                if validation_issue:
                    key = (norm_name, "UNCOMMON_DOSAGE", dosage_val)
                    if key not in conflict_set:
                        conflict_set.add(key)
                        conflicts.append({
                            "drug": norm_name,
                            "type": "UNCOMMON_DOSAGE",
                            "severity": SEVERITY["UNCOMMON_DOSAGE"],
                            "details": validation_issue,
                            "source": med.source
                        })

            # 🔹 First occurrence
            if norm_name not in med_map:
                med_map[norm_name] = {
                    "name": norm_name,
                    "dosage": norm_dosage,
                    "frequency": norm_freq,
                    "sources": [med.source],
                    "_priority": SOURCE_PRIORITY.get(med.source, 0)  # ✅ track priority
                }
                continue

            existing = med_map[norm_name]

            if med.source not in existing["sources"]:
                existing["sources"].append(med.source)

            current_priority = SOURCE_PRIORITY.get(med.source, 0)

            # 🔹 DOSAGE conflict
            if norm_dosage and existing["dosage"] and norm_dosage != existing["dosage"]:
                key = (norm_name, "DOSAGE_MISMATCH")
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        "drug": norm_name,
                        "type": "DOSAGE_MISMATCH",
                        "severity": SEVERITY["DOSAGE_MISMATCH"],
                        "values": [existing["dosage"], norm_dosage],
                        "sources": existing["sources"]
                    })

            # 🔹 FREQUENCY conflict
            if norm_freq and existing["frequency"] and norm_freq != existing["frequency"]:
                key = (norm_name, "FREQUENCY_MISMATCH")
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        "drug": norm_name,
                        "type": "FREQUENCY_MISMATCH",
                        "severity": SEVERITY["FREQUENCY_MISMATCH"],
                        "values": [existing["frequency"], norm_freq],
                        "sources": existing["sources"]
                    })

            # 🔥 PRIORITY-BASED UPDATE (FIXED)
            if norm_dosage and current_priority > existing["_priority"]:
                existing["dosage"] = norm_dosage

            if norm_freq and current_priority > existing["_priority"]:
                existing["frequency"] = norm_freq

            # 🔥 Update highest priority seen
            existing["_priority"] = max(existing["_priority"], current_priority)

    # 🔹 Step 3: Missing medication detection
    all_drugs = set(med_map.keys())

    for source_name, drugs in source_drug_map.items():
        missing = all_drugs - drugs

        for drug in missing:
            key = (drug, "MISSING_MEDICATION", source_name)
            if key not in conflict_set:
                conflict_set.add(key)
                conflicts.append({
                    "drug": drug,
                    "type": "MISSING_MEDICATION",
                    "severity": SEVERITY["MISSING_MEDICATION"],
                    "missing_in": source_name
                })

    # 🔹 Cleanup
    unified = []
    for med in med_map.values():
        med.pop("_priority", None)
        unified.append(med)

    return unified, conflicts