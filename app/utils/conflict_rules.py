import json
from pathlib import Path

with open(Path(__file__).parent / "conflict_rules.json") as f:
    RULES = json.load(f)

DOSAGE_LIMITS = RULES["dosage_limits"]
BLACKLISTED_COMBINATIONS = RULES["blacklisted_combinations"]