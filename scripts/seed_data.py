import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

MEDICATION_URL = f"{BASE_URL}/api/v1/medications/"
RECONCILE_URL = f"{BASE_URL}/api/v1/reconcile/"

# 🔹 Realistic drug dataset
DRUGS = [
    ("Paracetamol", ["500mg", "650mg"]),
    ("Ibuprofen", ["200mg", "400mg"]),
    ("Diclofenac", ["50mg"]),
    ("Metformin", ["500mg", "1000mg"]),
    ("Atorvastatin", ["10mg", "20mg"]),
    ("Amlodipine", ["5mg", "10mg"])
]

# 🔹 Frequencies (normalized + messy)
FREQUENCIES = [
    "BID", "OD",
    "once daily", "twice daily",
    "1-0-1", "0-1-0",
    "after food",
    "once at night",
    "stopped"
]

# 🔹 VALID sources (IMPORTANT)
SOURCES = ["EMR", "Patient", "Hospital"]

# 🔹 Names
FIRST_NAMES = ["Arjun", "Priya", "Rahul", "Anjali", "Kiran", "Sneha", "Amit"]
LAST_NAMES = ["Nair", "Sharma", "Reddy", "Menon", "Iyer", "Gupta"]

GENDERS = ["Male", "Female"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_med(patient_id, drug, conflict=None):
    name, dosages = drug

    dosage = random.choice(dosages)
    freq = random.choice(FREQUENCIES)

    if conflict == "dosage" and len(dosages) > 1:
        dosage = random.choice([d for d in dosages if d != dosage])

    if conflict == "frequency":
        freq = random.choice(["OD", "BID", "once daily"])

    if conflict == "stopped":
        freq = "stopped"

    return {
        "patient_id": patient_id,
        "name": name,
        "dosage": dosage,
        "frequency": freq,
        "source": random.choice(SOURCES)
    }


def generate_patient_data(pid):
    patient_id = f"p{pid}"

    meta = {
        "name": random_name(),
        "age": random.randint(25, 80),
        "gender": random.choice(GENDERS)
    }

    meds = []

    base_drugs = random.sample(DRUGS, random.randint(2, 4))

    for drug in base_drugs:
        meds.append(random_med(patient_id, drug))

        # 🔥 introduce variation (simulate multiple sources)
        if random.random() < 0.7:
            conflict_type = random.choice(
                ["none", "dosage", "frequency", "stopped"]
            )
            meds.append(random_med(patient_id, drug, conflict_type))

    return patient_id, meta, meds


def seed():
    print(f"\n🚀 Seeding system at: {BASE_URL}\n")

    success = 0
    fail = 0

    for i in range(1, 16):
        patient_id, meta, meds = generate_patient_data(i)

        print(f"\n👤 Seeding {patient_id} ({meta['name']})")

        # 🔹 STEP 1: Store medications
        for med in meds:
            try:
                res = requests.post(MEDICATION_URL, json=med)

                if res.status_code != 200:
                    print("❌ Med insert failed:", res.text)
                    fail += 1

            except Exception as e:
                print("❌ Exception inserting med:", e)
                fail += 1

        # 🔹 STEP 2: Run reconciliation (from DB)
        try:
            res = requests.post(RECONCILE_URL, json={
                "patient_id": patient_id
            })

            if res.status_code == 200:
                print("✅ Reconciled")
                success += 1
            else:
                print("❌ Reconcile failed:", res.text)
                fail += 1

        except Exception as e:
            print("❌ Exception reconcile:", e)
            fail += 1

    print("\n📊 Summary:")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {fail}")


if __name__ == "__main__":
    seed()