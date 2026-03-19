import re
from difflib import get_close_matches
from app.utils.drug_db import GENERIC_LOOKUP, BRAND_LOOKUP, SYNONYM_LOOKUP


# 🔹 Clean text helper
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    return re.sub(r'[^a-z0-9\s]', '', text)


# 🔹 Normalize dosage (robust)
def normalize_dosage(dosage: str):
    if not dosage:
        return None

    dosage = str(dosage).lower().strip()

    match = re.match(r"(\d*\.?\d+)\s*(mg|g)?", dosage)

    if not match:
        return None  # invalid → treated as missing

    value, unit = match.groups()
    value = float(value)

    if unit == "g":
        value *= 1000  # g → mg

    value = int(value)

    return f"{value}mg"


#  IMPROVED FREQUENCY NORMALIZATION
def normalize_frequency(freq: str):
    if not freq:
        return None

    freq = clean_text(freq)

    # 🔹 Canonical mapping
    freq_map = {
        # once daily
        "od": "once daily",
        "once": "once daily",
        "once daily": "once daily",
        "once a day": "once daily",
        "once in a day": "once daily",
        "1 per day": "once daily",
        "daily": "once daily",

        # twice daily
        "bid": "twice daily",
        "twice": "twice daily",
        "twice daily": "twice daily",
        "two times a day": "twice daily",
        "2 per day": "twice daily",

        # thrice daily
        "tid": "thrice daily",
        "thrice": "thrice daily",
        "three times a day": "thrice daily",
        "3 per day": "thrice daily",

        # stopped
        "stopped": "stopped",
        "discontinued": "stopped",
        "stop": "stopped"
    }

    # direct match
    if freq in freq_map:
        return freq_map[freq]

    #  pattern-based handling
    if re.search(r"\bonce\b.*\bday\b", freq):
        return "once daily"

    if re.search(r"\btwice\b.*\bday\b", freq):
        return "twice daily"

    if re.search(r"(three|thrice).*day", freq):
        return "thrice daily"

    #  numeric pattern (e.g., "2x/day")
    if re.search(r"1\s*[x/]\s*day", freq):
        return "once daily"

    if re.search(r"2\s*[x/]\s*day", freq):
        return "twice daily"

    if re.search(r"3\s*[x/]\s*day", freq):
        return "thrice daily"

    # fallback → keep cleaned value
    return freq


#  Normalize drug name
def normalize_name(name: str):
    name = clean_text(name)

    if not name:
        return None

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


#  Extract numeric dosage
def extract_dosage_value(dosage: str):
    if not dosage:
        return None

    dosage = dosage.lower().strip()

    match = re.match(r"(\d+)", dosage)

    if match:
        return int(match.group(1))

    return None