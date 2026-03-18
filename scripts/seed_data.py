import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL")
RECONCILE_ENDPOINT = os.getenv("RECONCILE_ENDPOINT")

if not BASE_URL or not RECONCILE_ENDPOINT:
    raise ValueError("Missing environment variables")

FULL_URL = BASE_URL + RECONCILE_ENDPOINT


DRUGS = [
    ("Paracetamol", ["500mg", "650mg"]),
    ("Ibuprofen", ["200mg", "400mg"]),
    ("Diclofenac", ["50mg"])
]

FREQUENCIES = ["BID", "OD", "twice daily", "once daily", "stopped"]
SOURCES = ["EMR", "Patient", "Discharge"]


def random_med(drug):
    name, dosages = drug
    return {
        "name": name,
        "dosage": random.choice(dosages),
        "frequency": random.choice(FREQUENCIES),
        "source": random.choice(SOURCES)
    }


def generate_patient(patient_id):
    sources = []

    for _ in range(random.randint(2, 3)):
        meds = []

        for drug in random.sample(DRUGS, random.randint(1, 3)):
            meds.append(random_med(drug))

        # 🔥 introduce duplicates
        if random.random() < 0.3:
            meds.append(meds[0])

        sources.append(meds)

    return {
        "patient_id": f"p{patient_id}",
        "sources": sources
    }


def seed():
    for i in range(1, 16):
        payload = generate_patient(i)

        res = requests.post(FULL_URL, json=payload)

        if res.status_code == 200:
            print(f"✅ Seeded patient p{i}")
        else:
            print(f"❌ Failed p{i}: {res.text}")


if __name__ == "__main__":
    seed()