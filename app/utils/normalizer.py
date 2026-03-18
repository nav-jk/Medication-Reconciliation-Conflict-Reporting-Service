import re
from difflib import get_close_matches
from app.utils.drug_db import GENERIC_LOOKUP, BRAND_LOOKUP, SYNONYM_LOOKUP


def clean_text(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r'[^a-z0-9\s]', '', text)

def normalize_dosage(dosage: str):
    if not dosage:
        return None

    dosage = dosage.lower().strip()

    import re
    match = re.match(r"(\d*\.?\d+)\s*(mg|g)?", dosage)

    if not match:
        return dosage

    value, unit = match.groups()
    value = float(value)

    if unit == "g":
        value *= 1000  # convert grams → mg

    # convert back to int safely
    value = int(value)

    return f"{value}mg"

def normalize_frequency(freq: str):
    if not freq:
        return None

    freq = freq.lower().strip()

    freq_map = {
        "od": "once daily",
        "bid": "twice daily",
        "tid": "thrice daily"
    }

    return freq_map.get(freq, freq)

def normalize_name(name: str):
    name = clean_text(name)

    # Exact generic
    if name in GENERIC_LOOKUP:
        return name

    # Brand → generic
    if name in BRAND_LOOKUP:
        return BRAND_LOOKUP[name]

    # Synonym → generic
    if name in SYNONYM_LOOKUP:
        return SYNONYM_LOOKUP[name]

    # Controlled fuzzy (ONLY generics)
    match = get_close_matches(name, GENERIC_LOOKUP, n=1, cutoff=0.85)
    if match:
        return match[0]

    return name

def extract_dosage_value(dosage: str):
    if not dosage:
        return None

    dosage = dosage.lower().strip()

    import re
    match = re.match(r"(\d+)", dosage)

    if match:
        return int(match.group(1))

    return None