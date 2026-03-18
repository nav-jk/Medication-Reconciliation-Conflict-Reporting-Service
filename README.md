# Medication Reconciliation & Conflict Reporting Service

## Overview

This system reconciles medication data from multiple sources (EMR, discharge summaries, patient reports), detects conflicts, and stores them with full history for audit and reporting.

The focus is on **clear modeling, robust conflict detection, and extensibility**.

---

## Architecture Overview

```
API Layer → Service Layer → Repository Layer → MongoDB
              ↓
       Conflict Detection Engine
              ↓
        Rule Engine (JSON)
```

### Components

* **API Layer**

  * FastAPI endpoints
  * Input validation

* **Service Layer**

  * Core reconciliation logic
  * Conflict detection

* **Repository Layer**

  * MongoDB access
  * Persistence

* **Rule Engine**

  * `conflict_rules.json`
  * Defines:

    * dosage limits
    * blacklisted combinations

---

## Data Model (MongoDB)

### Collection: `reconciliations`

Each document is a **snapshot**:

```json
{
  "patient_id": "p1",
  "timestamp": "...",
  "sources": [...],
  "unified": [...],
  "conflicts": [...]
}
```

---

### Versioning Strategy

* Each reconciliation creates a **new document**
* No updates → immutable history
* Enables:

  * audit trail
  * debugging
  * time-based analysis

---

### Indexing

* `{ patient_id: 1 }`
* `{ timestamp: -1 }`
* `{ "conflicts.status": 1 }`

---

## Conflict Detection

### Types

* DOSAGE_MISMATCH
* FREQUENCY_MISMATCH
* MEDICATION_STOPPED_CONFLICT
* BLACKLISTED_COMBINATION
* INCOMPLETE_DATA
* DUPLICATE_ENTRY
* MISSING_MEDICATION
* UNCOMMON_DOSAGE

---

## Conflict Rules Engine

Uses:

```
app/utils/conflict_rules.json
```

Defines:

* dosage limits
* unsafe drug combinations

👉 This separates **business rules from logic**

---

## Conflict Resolution

Each conflict contains:

```json
{
  "status": "unresolved",
  "resolved_at": null,
  "resolution_reason": null
}
```

Resolution is done via API.

---

## API Endpoints

### Reconciliation

```
POST /api/v1/reconcile/
GET  /api/v1/reconcile/{patient_id}
PATCH /api/v1/reconcile/resolve/{id}/{conflict_id}
```

---

### Reporting

```
GET /api/v1/reports/conflicts
```

#### Query Params

| Param         | Description       |
| ------------- | ----------------- |
| min_conflicts | minimum conflicts |
| days          | time window       |

---

## Setup

```bash
git clone <repo>
cd project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## Seed Data

```bash
python scripts/seed_data.py
```

---

## Tests

```bash
pytest -v
```

---

## Assumptions

* EMR is highest priority
* "stopped" indicates discontinued medication
* Blacklisted combinations are unsafe

---

## Trade-offs

| Decision             | Trade-off                   |
| -------------------- | --------------------------- |
| Denormalized DB      | Faster reads vs duplication |
| Static rules         | Simple vs limited           |
| Priority-based merge | Fast vs imperfect           |

---

## Limitations

* No real drug DB (RxNorm)
* No authentication
* No UI
* Static rules

---

## Future Improvements

* External drug APIs
* ML-based normalization
* UI dashboard
* Dynamic severity

---

## AI Usage

Used for:

* boilerplate generation
* debugging

Manually refined:

* data model
* conflict logic
* rule engine

Example disagreement:

* Replaced naive string matching with structured normalization

---

## Final Notes

This system prioritizes:

* clarity
* robustness
* extensibility

Designed to be easily extended into production systems.
