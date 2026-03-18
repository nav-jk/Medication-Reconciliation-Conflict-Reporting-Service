from app.utils.normalizer import normalize_name, normalize_dosage, normalize_frequency


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