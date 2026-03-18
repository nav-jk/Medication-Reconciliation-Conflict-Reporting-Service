import uuid
from datetime import datetime, timezone

from app.utils.normalizer import (
    normalize_name,
    normalize_dosage,
    normalize_frequency,
    extract_dosage_value
)
from app.utils.validator import validate_dosage
from app.utils.constants import SEVERITY, SOURCE_PRIORITY
from app.utils.conflict_rules import BLACKLISTED_COMBINATIONS


# 🔥 Standard conflict structure
def base_conflict():
    return {
        "id": str(uuid.uuid4()),
        "status": "unresolved",
        "resolved_at": None,
        "resolution_reason": None,
        "detected_at": datetime.now(timezone.utc).isoformat()
    }


def is_stopped(freq: str):
    if not freq:
        return False
    freq = freq.lower()
    return freq in ["stopped", "discontinued", "stop"]


def reconcile_medications(sources):
    med_map = {}
    conflicts = []
    conflict_set = set()
    source_drug_map = {}
    seen_entries = set()

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

            stopped_flag = is_stopped(norm_freq)

            # 🔥 DUPLICATE DETECTION
            entry_key = (med.source, norm_name, norm_dosage, norm_freq)

            if entry_key in seen_entries:
                key = (norm_name, "DUPLICATE_ENTRY", med.source)
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        **base_conflict(),
                        "drug": norm_name,
                        "type": "DUPLICATE_ENTRY",
                        "severity": "LOW",
                        "source": med.source
                    })
                continue

            seen_entries.add(entry_key)

            dosage_val = extract_dosage_value(norm_dosage)

            # 🔹 DOSAGE VALIDATION (RULE-BASED)
            if dosage_val:
                validation_issue = validate_dosage(norm_name, dosage_val)
                if validation_issue:
                    key = (norm_name, "UNCOMMON_DOSAGE", dosage_val)
                    if key not in conflict_set:
                        conflict_set.add(key)
                        conflicts.append({
                            **base_conflict(),
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
                    "frequency": None if stopped_flag else norm_freq,
                    "is_stopped": stopped_flag,
                    "sources": [med.source],
                    "_priority": SOURCE_PRIORITY.get(med.source, 0)
                }
                continue

            existing = med_map[norm_name]

            if med.source not in existing["sources"]:
                existing["sources"].append(med.source)

            current_priority = SOURCE_PRIORITY.get(med.source, 0)

            # 🔥 STOPPED MEDICATION CONFLICT
            if stopped_flag != existing.get("is_stopped", False):
                key = (norm_name, "MEDICATION_STOPPED_CONFLICT")
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        **base_conflict(),
                        "drug": norm_name,
                        "type": "MEDICATION_STOPPED_CONFLICT",
                        "severity": "HIGH",
                        "sources": existing["sources"],
                        "reason": "Medication active in one source but stopped in another"
                    })

            # 🔥 INCOMPLETE DATA
            if (existing["dosage"] is None and norm_dosage) or (existing["dosage"] and norm_dosage is None):
                key = (norm_name, "INCOMPLETE_DATA", "dosage")
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        **base_conflict(),
                        "drug": norm_name,
                        "type": "INCOMPLETE_DATA",
                        "severity": "LOW",
                        "field": "dosage",
                        "sources": existing["sources"]
                    })

            if (existing["frequency"] is None and norm_freq) or (existing["frequency"] and norm_freq is None):
                key = (norm_name, "INCOMPLETE_DATA", "frequency")
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        **base_conflict(),
                        "drug": norm_name,
                        "type": "INCOMPLETE_DATA",
                        "severity": "LOW",
                        "field": "frequency",
                        "sources": existing["sources"]
                    })

            # 🔹 DOSAGE conflict
            if norm_dosage and existing["dosage"] and norm_dosage != existing["dosage"]:
                key = (norm_name, "DOSAGE_MISMATCH")
                if key not in conflict_set:
                    conflict_set.add(key)
                    conflicts.append({
                        **base_conflict(),
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
                        **base_conflict(),
                        "drug": norm_name,
                        "type": "FREQUENCY_MISMATCH",
                        "severity": SEVERITY["FREQUENCY_MISMATCH"],
                        "values": [existing["frequency"], norm_freq],
                        "sources": existing["sources"]
                    })

            # 🔥 PRIORITY UPDATE
            if norm_dosage and current_priority > existing["_priority"]:
                existing["dosage"] = norm_dosage

            if norm_freq and current_priority > existing["_priority"]:
                existing["frequency"] = norm_freq

            if current_priority > existing["_priority"]:
                existing["is_stopped"] = stopped_flag

            existing["_priority"] = max(existing["_priority"], current_priority)

    # 🔥 STEP 3: BLACKLISTED COMBINATIONS (REPLACES CLASS LOGIC)
    drugs_present = list(med_map.keys())

    for combo in BLACKLISTED_COMBINATIONS:
        if all(drug in drugs_present for drug in combo):
            key = tuple(sorted(combo)) + ("BLACKLISTED_COMBINATION",)

            if key not in conflict_set:
                conflict_set.add(key)

                conflicts.append({
                    **base_conflict(),
                    "type": "BLACKLISTED_COMBINATION",
                    "severity": "HIGH",
                    "drugs": combo,
                    "reason": "Known unsafe drug combination"
                })

    # 🔹 Step 4: Missing meds
    all_drugs = set(med_map.keys())

    for source_name, drugs in source_drug_map.items():
        missing = all_drugs - drugs

        for drug in missing:
            key = (drug, "MISSING_MEDICATION", source_name)
            if key not in conflict_set:
                conflict_set.add(key)
                conflicts.append({
                    **base_conflict(),
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