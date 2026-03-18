import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "drugs.json"

with open(DATA_PATH, "r") as f:
    DRUG_DB = json.load(f)

GENERIC_LOOKUP = set(DRUG_DB.keys())
BRAND_LOOKUP = {}
SYNONYM_LOOKUP = {}

for generic, data in DRUG_DB.items():
    for brand in data.get("brands", []):
        BRAND_LOOKUP[brand] = generic
    for syn in data.get("synonyms", []):
        SYNONYM_LOOKUP[syn] = generic