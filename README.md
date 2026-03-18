# Medication Reconciliation & Conflict Reporting Service

## Scenario

For a chronic‑care patient, different systems often provide **conflicting medication lists**: the dialysis clinic's EMR, a recent hospital discharge summary, and patient verbal reports. The service ingests lists from multiple sources, maintains a longitudinal record, and surfaces unresolved conflicts for clinicians and for reporting.

---

## Core Requirements

### MongoDB Data Model

- Patients and **longitudinal medication snapshots**.
- Multiple sources per snapshot (`clinic_emr`, `hospital_discharge`, `patient_reported`).
- **Versioning / history** — ability to view how a medication list changed over time.
- Simple notion of **"resolved" vs "unresolved"** conflicts.

### Python / FastAPI Service

- **Ingest** a medication list for a given patient and source (REST endpoint).
- **Normalize** incoming items (lowercasing names, trimming units) into a canonical internal structure.
- **Detect conflicts** across sources for the same patient:
    - Same drug, different dose.
    - Drugs from the same class that should not be combined.
    - Medication present in one source but explicitly stopped in another.
- **Store conflict records** in an auditable structure.