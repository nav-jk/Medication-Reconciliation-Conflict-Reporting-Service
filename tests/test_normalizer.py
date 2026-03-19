from app.utils.normalizer import normalize_name, normalize_dosage, normalize_frequency
from app.services.reconciliation_service import reconcile_medications

class DummyMed:
    def __init__(self, name, dosage, frequency, source):
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.source = source


def test_empty_name():
    sources = [[DummyMed("", "500mg", "BID", "EMR")]]
    unified, conflicts = reconcile_medications(sources)

    assert len(unified) == 0


def test_invalid_dosage():
    sources = [[DummyMed("Paracetamol", "abc", "BID", "EMR")]]
    unified, conflicts = reconcile_medications(sources)

    assert any(c["type"] == "INCOMPLETE_DATA" for c in conflicts)


def test_random_frequency():
    sources = [[DummyMed("Paracetamol", "500mg", "randomtext", "EMR")]]
    unified, conflicts = reconcile_medications(sources)

    assert unified[0]["frequency"] == "randomtext"


def test_null_values():
    sources = [[DummyMed("Paracetamol", None, None, "EMR")]]
    unified, conflicts = reconcile_medications(sources)

    assert unified[0]["dosage"] is None

def test_name_normalization():
    assert normalize_name("PCM") == "paracetamol"
    assert normalize_name("Crocin") == "paracetamol"
    assert normalize_name("paracetmol") == "paracetamol"  # typo


def test_dosage_normalization():
    assert normalize_dosage("500 mg") == "500mg"
    assert normalize_dosage("0.5g") == "500mg"


def test_frequency_normalization():
    assert normalize_frequency("BID") == "twice daily"
    assert normalize_frequency("OD") == "once daily"
