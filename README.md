# Medication Reconciliation & Conflict Reporting Service

**Track:** Backend / Data Engineering  
**Stack:** FastAPI · MongoDB · Python  
**Author:** Navaneet J  
**Time Spent:** ~9–10 hours

---

## Overview

This project implements a **Medication Reconciliation & Conflict Reporting Service** designed for chronic-care workflows (e.g., dialysis patients).

Different sources (EMR, hospital discharge, patient-reported) often provide conflicting medication data. This system:

- Ingests medication lists from multiple sources
- Normalizes and reconciles them into a unified view
- Detects conflicts across sources
- Maintains versioned history (longitudinal snapshots)
- Allows conflict resolution with audit trail
- Provides clinic-level analytics and reporting

---

## Key Features

### 🔹 Core Functionality

- Multi-source medication ingestion
- Canonical normalization (name, dosage, frequency)
- Conflict detection:
  - Dosage mismatch
  - Frequency mismatch
  - Missing/incomplete data
  - Duplicate entries
  - Stopped vs active conflict
  - Blacklisted combinations (via static rules)

### 🔹 Versioning (Longitudinal Tracking)

- Each reconciliation creates a new version
- Full history preserved per patient
- Snapshots include:
  - Unified medications
  - Conflicts
  - Timestamp
  - Action (`created` / `updated`)

### 🔹 Conflict Resolution

- Resolve conflicts with:
  - `corrected_field` (name, dosage, frequency)
  - `corrected_value`
  - `resolution_reason`
- Updates:
  - Conflict status → `resolved`
  - Unified medication list
  - Audit metadata (timestamp + reason)

### 🔹 Multi-Clinic Support

- Each reconciliation tagged with `clinic_id`
- Enables cross-clinic analytics

### 🔹 Reporting & Aggregation

- Patients with unresolved conflicts per clinic
- Conflict summary across clinics (time-window based)

---

## Architecture Overview

```
Frontend (HTML/JS)
        ↓
FastAPI Layer (Routes)
        ↓
Service Layer (Reconciliation Logic)
        ↓
Repository Layer (MongoDB)
        ↓
MongoDB (Versioned Documents)
```

**Data Flow:**

1. Client submits medication lists
2. Service normalizes + detects conflicts
3. Repository stores new version snapshot
4. Aggregation queries operate on latest version

---

## Data Model

### 🔹 Collection: `reconciliations`

```json
{
  "_id": "ObjectId",
  "patient_id": "p1",
  "clinic_id": "clinic_a",
  "sources": ["..."],
  "latest_version": 3,
  "versions": [
    {
      "version": 1,
      "timestamp": "...",
      "unified": ["..."],
      "conflicts": ["..."],
      "action": "created"
    },
    {
      "version": 2,
      "timestamp": "...",
      "unified": ["..."],
      "conflicts": ["..."],
      "action": "updated"
    }
  ]
}
```

### 🔹 Conflict Structure

```json
{
  "id": "uuid",
  "drug": "Paracetamol",
  "type": "DOSAGE_MISMATCH",
  "severity": "HIGH",
  "values": ["500mg", "650mg"],
  "status": "unresolved",
  "resolved_at": null,
  "resolution_reason": null,
  "corrected_field": null,
  "corrected_value": null
}
```

---

## Indexing Strategy

```js
db.reconciliations.createIndex({ patient_id: 1 })
db.reconciliations.createIndex({ clinic_id: 1 })
db.reconciliations.createIndex({ "versions.timestamp": -1 })
```

**Rationale:**

- Fast patient lookup
- Efficient clinic-level aggregation
- Time-based queries for reports

---

## API Endpoints

### 🔹 Reconciliation

**`POST /api/v1/reconcile/`**  
Ingest and reconcile medications

**`GET /api/v1/reconcile/{patient_id}`**  
Fetch full patient history (with versions)

---

### 🔹 Conflict Resolution

**`PATCH /api/v1/reconcile/resolve/{reconciliation_id}/{conflict_id}`**

Payload:
```json
{
  "field": "dosage",
  "corrected_value": "500mg",
  "reason": "Doctor confirmed"
}
```

---

### 🔹 Reports

**Patients with conflicts**  
`GET /api/v1/reports/clinic/{clinic_id}/patients-with-conflicts`

**Conflict summary**  
`GET /api/v1/reports/clinic/conflict-summary?days=30&min_conflicts=2`

---

## Tests

```bash
pytest -v
```

Coverage includes:

- Reconciliation logic
- Conflict detection
- Versioning behavior
- Conflict resolution updates
- Aggregation endpoints

---

## Seed Script

```bash
python scripts/seed_data.py
```

Generates:

- 10–20 patients
- Multiple versions per patient
- Realistic noisy data
- Forced conflicts (dosage/frequency/stopped)

---

## Setup Instructions

```bash
git clone <repo>
cd project

python -m venv venv
venv\Scripts\activate  # Windows

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Assumptions & Design Decisions

1. **No single source of truth**
   - Conflicts are not auto-resolved
   - Manual resolution required with audit trail

2. **Versioning over mutation**
   - Every reconciliation creates a new snapshot
   - Enables full history tracking

3. **Denormalized structure**
   - Faster reads for aggregation
   - Trade-off: duplication across versions

4. **Static conflict rules**
   - JSON-based rules instead of external drug DB
   - Keeps system simple and deterministic

---

## Trade-offs

| Decision | Trade-off |
|---|---|
| Versioned documents | Larger document size |
| Denormalization | Data duplication |
| No external drug DB | Limited clinical accuracy |
| Simple normalization | Some edge cases missed |

---

## Known Limitations

- No authentication / authorization
- Limited drug normalization (basic fuzzy matching)
- No real drug interaction database
- No pagination for large datasets
- Conflict severity is heuristic

---

## What I Would Do Next

- Add real drug database (RxNorm / SNOMED)
- Introduce authentication & roles
- Build dashboard for clinicians
- Add streaming updates (real-time)
- Improve normalization (ML/NLP-based)
- Add caching for aggregation endpoints

---

## AI Usage

**Used for:**
- Boilerplate FastAPI setup
- Debugging aggregation issues
- Structuring test cases

**Manually reviewed:**
- Aggregation pipelines
- Data model decisions
- Conflict resolution logic

**Disagreement example:**

> AI initially suggested using flat schema for conflicts.  
> I rejected this and implemented versioned snapshots, as it better models real-world medical history.

---

## Demo

Include:
- Screenshots of UI (reconciliation + conflicts)
- OR screen recording

---

## Submission Checklist

- [ ] Clean Git history
- [ ] Working FastAPI backend
- [ ] MongoDB schema with versioning
- [ ] Seed script
- [ ] Tests for core logic
- [ ] Aggregation endpoints
- [ ] README (this document)

---

## Final Note

This system is designed with real-world healthcare data challenges in mind:
- inconsistent inputs
- lack of ground truth
- need for auditability

The focus was on **clarity**, **extensibility**, and **robustness**, rather than over-engineering.