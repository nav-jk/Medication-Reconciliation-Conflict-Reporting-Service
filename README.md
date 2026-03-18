# Medication Reconciliation & Conflict Reporting Service

## Overview

This project implements a backend service to **ingest, normalize, reconcile, and analyze medication data** from multiple sources for chronic-care patients.

In real-world healthcare systems, medication lists from different sources (EMR, discharge summaries, patient-reported data) often conflict. This service detects such inconsistencies, stores them with audit history, and provides reporting capabilities.

---

## Tech Stack

* **Backend:** FastAPI
* **Database:** MongoDB
* **Language:** Python 3.12
* **Async DB Driver:** Motor
* **Validation:** Pydantic v2
* **Testing:** Pytest

---

## System Architecture

### High-Level Flow

```
Request → API Layer → Service Layer → Repository Layer → MongoDB
                     ↓
              Conflict Detection Engine
```

### Layers

* **API Layer (`/api/v1/endpoints`)**

  * Handles HTTP requests
  * Input validation using Pydantic schemas

* **Service Layer (`services/`)**

  * Core business logic
  * Normalization + reconciliation + conflict detection

* **Repository Layer (`db/repositories/`)**

  * Database interaction
  * Encapsulates MongoDB queries

* **Utils Layer (`utils/`)**

  * Drug normalization
  * Validation rules
  * Static drug database

---

## MongoDB Data Model

### Collection: `reconciliations`

```json
{
  "_id": ObjectId,
  "patient_id": "p1",
  "timestamp": "2026-03-18T10:44:16Z",
  "sources": [...],
  "unified": [...],
  "conflicts": [
    {
      "id": "uuid",
      "type": "DOSAGE_MISMATCH",
      "status": "unresolved",
      "severity": "HIGH",
      "detected_at": "...",
      "resolved_at": null,
      "resolution_reason": null
    }
  ]
}
```

---

### Key Design Decisions

#### 1. Snapshots Instead of Updates

* Each reconciliation request creates a **new document**
* Enables **full history tracking**
* No in-place mutation

#### 2. Versioning Strategy

* Versioning is implicit via:

  * `timestamp`
  * multiple documents per patient
* Allows:

  * time-based queries
  * rollback/debugging
  * audit trails

#### 3. Denormalization Choice

* Stored:

  * sources
  * unified output
  * conflicts
* Tradeoff:

  * ✅ Faster reads
  * ❌ Slight duplication

---

### Indexing Strategy

Recommended indexes:

```js
{ patient_id: 1 }
{ timestamp: -1 }
{ "conflicts.status": 1 }
```

---

## Core Features

### 1. Ingestion & Normalization

* Converts:

  * `PCM → paracetamol`
  * `0.5g → 500mg`
  * `BID → twice daily`

* Handles:

  * typos (fuzzy matching)
  * brand vs generic mapping

---

### 2. Conflict Detection

#### Supported Conflict Types

| Type                        | Description                 | Severity |
| --------------------------- | --------------------------- | -------- |
| DOSAGE_MISMATCH             | Same drug, different dose   | HIGH     |
| FREQUENCY_MISMATCH          | Different frequency         | MEDIUM   |
| DRUG_CLASS_CONFLICT         | Same class drugs (NSAIDs)   | HIGH     |
| MEDICATION_STOPPED_CONFLICT | Active vs stopped           | HIGH     |
| INCOMPLETE_DATA             | Missing fields              | LOW      |
| DUPLICATE_ENTRY             | Duplicate entries in source | LOW      |
| MISSING_MEDICATION          | Present in one source only  | MEDIUM   |
| UNCOMMON_DOSAGE             | Outside safe range          | MEDIUM   |

---

### 3. Conflict Resolution System

Each conflict includes:

```json
{
  "status": "unresolved",
  "resolved_at": null,
  "resolution_reason": null
}
```

PATCH endpoint allows:

```http
PATCH /resolve/{reconciliation_id}/{conflict_id}
```

---

### 4. Drug Interaction Rules

Implemented via `drugs.json`:

* Drug class mapping
* Detects unsafe combinations:

  * e.g. **Ibuprofen + Diclofenac**

---

### 5. Reporting / Aggregation

#### Endpoint

```http
GET /api/v1/reports/conflicts
```

#### Filters

* `min_conflicts`
* `days`

#### Example

```http
GET /api/v1/reports/conflicts?min_conflicts=2&days=30
```

---

## API Endpoints

### Health

```
GET /api/v1/health/
```

---

### Medications

```
POST /api/v1/medications/
GET  /api/v1/medications/{patient_id}
```

---

### Reconciliation

```
POST /api/v1/reconcile/
GET  /api/v1/reconcile/{patient_id}
PATCH /api/v1/reconcile/resolve/{id}/{conflict_id}
```

---

### Reports

```
GET /api/v1/reports/conflicts
```

---

## Setup Instructions

### 1. Clone Repo

```bash
git clone <repo-url>
cd medication-reconciliation-service
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup Environment Variables

Create `.env`:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=medicine
API_BASE_URL=http://127.0.0.1:8000
RECONCILE_ENDPOINT=/api/v1/reconcile/
```

---

### 5. Run Server

```bash
uvicorn app.main:app --reload
```

---

### 6. Access Docs

```
http://127.0.0.1:8000/docs
```

---

## Seed Data

```bash
python scripts/seed_data.py
```

Generates:

* 10–20 patients
* multiple sources
* realistic conflicts

---

## Testing

```bash
pytest -v
```

### Coverage Includes:

* Conflict detection edge cases
* Deduplication logic
* Drug interactions
* Stopped medications
* Data validation
* Conflict structure consistency

---

## Assumptions

* EMR is more reliable than Patient-reported data
* Frequency "stopped" indicates discontinued medication
* Same drug class implies potential interaction risk
* Conflict resolution is manual (no auto-resolution)

---

## Trade-offs

| Decision                | Trade-off                        |
| ----------------------- | -------------------------------- |
| Denormalized storage    | Faster reads vs duplication      |
| Static drug DB          | Simpler vs less scalable         |
| Heuristic normalization | Fast vs not medically exhaustive |
| Priority-based merge    | Simple vs not always correct     |

---

## Limitations

* No real drug interaction database
* No authentication/authorization
* No clinician workflow UI
* Severity is partly static (can be dynamic)
* No ML-based normalization

---

## Future Improvements

* Integrate RxNorm / openFDA
* Dynamic severity scoring
* Conflict auto-resolution suggestions
* UI dashboard for clinicians
* Streaming ingestion (Kafka)

---

## AI Usage

### Used for:

* Boilerplate generation
* Debugging Pydantic + FastAPI issues
* Structuring reconciliation logic

### Manual Changes:

* Conflict system redesign
* Data model decisions
* Normalization + priority logic

### Example disagreement:

Initial approach suggested simple string matching for drugs.
This was replaced with:

* synonym mapping
* brand → generic conversion
* fuzzy matching

---

## Final Notes

This system is designed with a focus on:

* **clarity of modeling**
* **robust conflict detection**
* **real-world extensibility**

