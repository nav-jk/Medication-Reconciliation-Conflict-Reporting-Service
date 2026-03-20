import re
from difflib import get_close_matches
from app.utils.drug_db import GENERIC_LOOKUP, BRAND_LOOKUP, SYNONYM_LOOKUP


# 🔹 Clean text helper
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    return re.sub(r'[^a-z0-9\s]', '', text)


# 🔥 Normalize drug name (robust)
def normalize_name(name: str):
    name = clean_text(name)

    if not name:
        return None

    # exact generic
    if name in GENERIC_LOOKUP:
        return name

    # brand → generic
    if name in BRAND_LOOKUP:
        return BRAND_LOOKUP[name]

    # synonym → generic
    if name in SYNONYM_LOOKUP:
        return SYNONYM_LOOKUP[name]

    # 🔥 fuzzy match ONLY against generics
    match = get_close_matches(name, GENERIC_LOOKUP, n=1, cutoff=0.85)
    if match:
        return match[0]

    return name


# 🔥 Normalize dosage (real-world robust)
def normalize_dosage(dosage: str):
    if not dosage:
        return None

    dosage = str(dosage).lower().strip()

    # handle mg, g, mcg
    match = re.match(r"(\d*\.?\d+)\s*(mg|g|mcg)?", dosage)

    if not match:
        return None

    value, unit = match.groups()
    value = float(value)

    if unit == "g":
        value *= 1000
    elif unit == "mcg":
        value /= 1000

    value = int(round(value))

    return f"{value}mg"


# 🔥 Extract numeric dosage
def extract_dosage_value(dosage: str):
    if not dosage:
        return None

    match = re.match(r"(\d+)", dosage)
    return int(match.group(1)) if match else None


# 🔥 Advanced frequency normalization
def normalize_frequency(freq: str):
    if not freq:
        return None

    raw = freq
    freq = clean_text(freq)

    freq_map = {
        # once daily
        "od": "once daily",
        "once": "once daily",
        "daily": "once daily",
        "once daily": "once daily",
        "once a day": "once daily",

        # twice daily
        "bid": "twice daily",
        "twice": "twice daily",
        "twice daily": "twice daily",

        # thrice daily
        "tid": "thrice daily",
        "thrice": "thrice daily",
        "thrice daily": "thrice daily",

        # bedtime / night
        "hs": "once daily",
        "at night": "once daily",

        # SOS / PRN
        "sos": "as needed",
        "prn": "as needed",

        # stopped
        "stopped": "stopped",
        "discontinued": "stopped",
        "stop": "stopped"
    }

    if freq in freq_map:
        return freq_map[freq]

    # 🔥 pattern detection
    if re.search(r"\bonce\b.*\bday\b", freq):
        return "once daily"

    if re.search(r"\btwice\b.*\bday\b", freq):
        return "twice daily"

    if re.search(r"(three|thrice).*day", freq):
        return "thrice daily"

    # 🔥 numeric patterns
    if re.search(r"1\s*[x/]\s*day", freq):
        return "once daily"

    if re.search(r"2\s*[x/]\s*day", freq):
        return "twice daily"

    if re.search(r"3\s*[x/]\s*day", freq):
        return "thrice daily"

    # 🔥 Indian prescription pattern (VERY IMPORTANT)
    if re.match(r"[01]-[01]-[01]", raw):
        parts = raw.split("-")
        count = sum(int(x) for x in parts if x.isdigit())

        if count == 1:
            return "once daily"
        elif count == 2:
            return "twice daily"
        elif count == 3:
            return "thrice daily"

    return freq