import requests
import random
import os
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

MEDICATION_URL = f"{BASE_URL}/api/v1/medications/"
RECONCILE_URL = f"{BASE_URL}/api/v1/reconcile/"


#  Clinics
CLINICS = ["clinic_a", "clinic_b", "clinic_c"]


DRUGS = [
    ("Paracetamol", ["500mg", "650mg"], ["crocin", "pcm"]),
    ("Ibuprofen", ["200mg", "400mg"], ["brufen"]),
    ("Diclofenac", ["50mg"], ["voveran"]),
    ("Metformin", ["500mg", "1000mg"], ["glycomet"]),
    ("Amlodipine", ["5mg", "10mg"], ["amlong"]),
    ("Atorvastatin", ["10mg", "20mg"], ["atorva"]),
    ("Aspirin", ["75mg", "150mg"], ["ecosprin"]),
    ("Clopidogrel", ["75mg"], ["plavix"]),
    ("Amoxicillin", ["250mg", "500mg"], ["amoxil"]),
    ("Pantoprazole", ["20mg", "40mg"], ["pantocid"])
]


FREQUENCIES = [
    "OD", "BID", "TID",
    "once daily", "twice daily",
    "1-0-1", "0-1-0", "1-1-1",
    "SOS", "PRN",
    "HS",
    "after food",
    "stopped"
]


SOURCES = ["EMR", "Patient", "Hospital"]


def messy_name(generic, brands):
    choice = random.choice(["generic", "brand", "typo"])

    if choice == "brand" and brands:
        return random.choice(brands)

    if choice == "typo":
        return generic[:max(3, len(generic)-1)]

    return generic


def random_med(patient_id, drug, conflict=None):
    name, dosages, brands = drug

    med_name = messy_name(name, brands)
    dosage = random.choice(dosages)
    freq = random.choice(FREQUENCIES)

    if conflict == "dosage" and len(dosages) > 1:
        dosage = random.choice([d for d in dosages if d != dosage])

    if conflict == "frequency":
        freq = random.choice(["OD", "BID", "1-0-1"])

    if conflict == "stopped":
        freq = "stopped"

    return {
        "patient_id": patient_id,
        "name": med_name,
        "dosage": dosage,
        "frequency": freq,
        "source": random.choice(SOURCES)
    }


def generate_med_batch(patient_id, base_drugs):
    meds = []

    for drug in base_drugs:
        meds.append(random_med(patient_id, drug))

        if random.random() < 0.7:
            conflict_type = random.choice(
                ["none", "dosage", "frequency", "stopped"]
            )
            meds.append(random_med(patient_id, drug, conflict_type))

    return meds


def seed():
    print(f"\n Seeding system at: {BASE_URL}\n")

    success = 0
    fail = 0

    for i in range(1, 16):
        patient_id = f"p{i}"
        clinic_id = random.choice(CLINICS)

        print(f"\n👤 Seeding {patient_id} | Clinic: {clinic_id}")

        base_drugs = random.sample(DRUGS, random.randint(3, 5))

        for step in range(1, random.randint(2, 4)):
            print(f"  ⏳ Step {step}")

            meds = generate_med_batch(patient_id, base_drugs)
            # 🔹 Insert medications
            for med in meds:
                try:
                    res = requests.post(MEDICATION_URL, json=med)
                    if res.status_code != 200:
                        print("   Med insert failed:", res.text)
                        fail += 1
                except Exception as e:
                    print("   Exception inserting med:", e)
                    fail += 1

            #  Group meds into sources for reconciliation
            source_map = {}
            for m in meds:
                source_map.setdefault(m["source"], []).append({
                    "name": m["name"],
                    "dosage": m["dosage"],
                    "frequency": m["frequency"],
                    "source": m["source"]
                })

            sources_payload = list(source_map.values())

            #  Reconcile with clinic_id
            try:
                res = requests.post(RECONCILE_URL, json={
                    "patient_id": patient_id,
                    "clinic_id": clinic_id,
                    "sources": sources_payload
                })

                if res.status_code == 200:
                    print(f"   Reconciled (version {step})")
                    success += 1
                else:
                    print("   Reconcile failed:", res.text)
                    fail += 1

            except Exception as e:
                print("   Exception reconcile:", e)
                fail += 1

            time.sleep(0.2)

    print("\n Summary:")
    print(f"Success: {success}")
    print(f"Failed: {fail}")


if __name__ == "__main__":
    seed()