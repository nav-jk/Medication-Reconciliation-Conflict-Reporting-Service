import pytest
from app.services.reconciliation_service import reconcile_medications


class DummyMed:
    def __init__(self, name, dosage, frequency, source):
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.source = source


# 🔹 Helper
def make_sources(*groups):
    return [[DummyMed(*m) for m in group] for group in groups]


# 🔥 1. Duplicate detection
def test_duplicate_detection():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR"),
         ("Paracetamol", "500mg", "BID", "EMR")]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "DUPLICATE_ENTRY" for c in conflicts)


# 🔥 2. Source priority
def test_source_priority():
    sources = make_sources(
        [("Paracetamol", "650mg", "BID", "Patient")],
        [("Paracetamol", "500mg", "BID", "EMR")]
    )

    unified, _ = reconcile_medications(sources)

    assert unified[0]["dosage"] == "500mg"


# 🔥 3. Incomplete data
def test_incomplete_data():
    sources = make_sources(
        [("Paracetamol", None, "BID", "EMR")],
        [("Paracetamol", "500mg", "BID", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "INCOMPLETE_DATA" for c in conflicts)


# 🔥 4. Stopped medication
def test_stopped_medication():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR")],
        [("Paracetamol", "500mg", "stopped", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "MEDICATION_STOPPED_CONFLICT" for c in conflicts)


# 🔥 5. Drug class conflict
def test_drug_class_conflict():
    sources = make_sources(
        [
            ("Ibuprofen", "200mg", "OD", "EMR"),
            ("Diclofenac", "50mg", "OD", "EMR")
        ]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "DRUG_CLASS_CONFLICT" for c in conflicts)


# 🔥 6. Dosage mismatch
def test_dosage_mismatch():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR")],
        [("Paracetamol", "650mg", "BID", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "DOSAGE_MISMATCH" for c in conflicts)


# 🔥 7. Frequency mismatch
def test_frequency_mismatch():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR")],
        [("Paracetamol", "500mg", "OD", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "FREQUENCY_MISMATCH" for c in conflicts)


# 🔥 8. Missing medication
def test_missing_medication():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR")],
        [("Ibuprofen", "200mg", "OD", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "MISSING_MEDICATION" for c in conflicts)


# 🔥 9. Conflict structure
def test_conflict_structure():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR")],
        [("Paracetamol", "650mg", "BID", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    c = conflicts[0]

    assert "id" in c
    assert "status" in c
    assert "detected_at" in c


# 🔥 10. No false positives
def test_no_conflict_case():
    sources = make_sources(
        [("Paracetamol", "500mg", "BID", "EMR")],
        [("PCM", "500mg", "twice daily", "Patient")]
    )

    _, conflicts = reconcile_medications(sources)

    assert len(conflicts) == 0