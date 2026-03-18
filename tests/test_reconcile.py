from app.services.reconciliation_service import reconcile_medications


class DummyMed:
    def __init__(self, name, dosage, frequency, source):
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.source = source


def test_basic_merge():
    sources = [
        [DummyMed("PCM", "500mg", "BID", "EMR")],
        [DummyMed("Paracetamol", "0.5g", "twice daily", "Patient")]
    ]

    unified, conflicts = reconcile_medications(sources)

    assert len(unified) == 1
    assert unified[0]["name"] == "paracetamol"
    assert conflicts == []


def test_dosage_conflict():
    sources = [
        [DummyMed("Paracetamol", "500mg", "BID", "EMR")],
        [DummyMed("Paracetamol", "650mg", "BID", "Patient")]
    ]

    unified, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "DOSAGE_MISMATCH" for c in conflicts)


def test_frequency_conflict():
    sources = [
        [DummyMed("Ibuprofen", "200mg", "OD", "EMR")],
        [DummyMed("Brufen", "200mg", "BID", "Patient")]
    ]

    unified, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "FREQUENCY_MISMATCH" for c in conflicts)


def test_uncommon_dosage():
    sources = [
        [DummyMed("Paracetamol", "700mg", "BID", "EMR")]
    ]

    unified, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "UNCOMMON_DOSAGE" for c in conflicts)

def test_missing_medication():
    sources = [
        [
            DummyMed("Paracetamol", "500mg", "BID", "EMR"),
            DummyMed("Ibuprofen", "200mg", "OD", "EMR")
        ],
        [
            DummyMed("Paracetamol", "500mg", "BID", "Patient")
        ]
    ]

    unified, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "MISSING_MEDICATION" for c in conflicts)

def test_duplicate_entry():
    sources = [
        [
            DummyMed("Paracetamol", "500mg", "BID", "EMR"),
            DummyMed("Paracetamol", "500mg", "BID", "EMR")
        ]
    ]

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "DUPLICATE_ENTRY" for c in conflicts)

def test_source_priority():
    sources = [
        [DummyMed("Paracetamol", "650mg", "BID", "Patient")],
        [DummyMed("Paracetamol", "500mg", "BID", "EMR")]
    ]

    unified, _ = reconcile_medications(sources)

    assert unified[0]["dosage"] == "500mg"

def test_missing_medication():
    sources = [
        [
            DummyMed("Paracetamol", "500mg", "BID", "EMR"),
            DummyMed("Ibuprofen", "200mg", "OD", "EMR")
        ],
        [
            DummyMed("Paracetamol", "500mg", "BID", "Patient")
        ]
    ]

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "MISSING_MEDICATION" for c in conflicts)

def test_incomplete_data():
    sources = [
        [DummyMed("Paracetamol", None, "BID", "EMR")],
        [DummyMed("Paracetamol", "500mg", "BID", "Patient")]
    ]

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "INCOMPLETE_DATA" for c in conflicts)

def test_incomplete_data():
    sources = [
        [DummyMed("Paracetamol", None, "BID", "EMR")],
        [DummyMed("Paracetamol", "500mg", "BID", "Patient")]
    ]

    _, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "INCOMPLETE_DATA" for c in conflicts)

