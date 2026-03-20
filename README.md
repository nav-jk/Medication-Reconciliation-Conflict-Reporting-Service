# Medication Reconciliation & Conflict Reporting Service


This project implements a **Medication Reconciliation & Conflict Reporting Service** designed for chronic-care workflows (e.g., dialysis patients).

Different sources (EMR, hospital discharge, patient-reported) often provide conflicting medication data. This system:

- Ingests medication lists from multiple sources
- Normalizes and reconciles them into a unified view
- Detects conflicts across sources
- Maintains versioned history (longitudinal snapshots)
- Allows conflict resolution with audit trail
- Provides clinic-level analytics and reporting

---

# Key Features — Detailed Logic & System Behavior

This section explains how the system actually works internally, including normalization, conflict detection, and data handling.
The goal is to make the system understandable even without running it.

---

## Core Functionality (Detailed)

### 1. Multi-Source Medication Ingestion

Each request contains:

```json
{
  "patient_id": "p1",
  "clinic_id": "clinic_a",
  "sources": [
    [ {"meds from EMR"} ],
    [ {"meds from Patient"} ],
    [ {"meds from Hospital"} ]
  ]
}
```

**Design Choice:**
- Sources are grouped arrays → preserves origin context
- Each medication retains its `source` field

---

### 2. Canonical Normalization

Incoming medical data is highly inconsistent. The system normalizes three key fields:

---

#### a. Medication Name Normalization

Steps:
1. Lowercasing + trimming
2. Mapping:
   - brand → generic (`crocin` → `paracetamol`)
   - synonyms → canonical name
3. Fuzzy matching (`difflib.get_close_matches`)
   - Handles typos like `"paracetmol"`

Example:

| Input | Normalized |
|---|---|
| `"Crocin"` | `"paracetamol"` |
| `"PCM"` | `"paracetamol"` |
| `"paracetmol"` | `"paracetamol"` |

---

#### b. Dosage Normalization

Uses regex:

```
(\d*\.?\d+)\s*(mg|g)?
```

Steps:
1. Extract numeric value
2. Convert to standard unit (`mg`)
3. Store as string (`"500mg"`)

Example:

| Input | Normalized |
|---|---|
| `"0.5g"` | `"500mg"` |
| `"500 mg"` | `"500mg"` |

---

#### c. Frequency Normalization

Maps multiple formats into canonical form:

| Input | Normalized |
|---|---|
| `"OD"`, `"daily"` | `"once daily"` |
| `"BID"`, `"1-0-1"` | `"twice daily"` |
| `"TID"` | `"thrice daily"` |

Special handling:
- `"stopped"` → sets `is_stopped = True`

---

### 3. Unified Medication Generation

After normalization:
- Medications are grouped by normalized drug name
- Aggregated into a single unified list

Each unified entry contains:
- `name`
- `dosage` (if consistent)
- `frequency` (if consistent)
- All contributing sources

---

### 4. Conflict Detection Logic

Conflicts are detected per drug across sources.

---

#### 1. Dosage Mismatch

**Condition:** Same drug + different dosage values

```
EMR: 500mg
Patient: 650mg
→ conflict
```

---

#### 2. Frequency Mismatch

**Condition:** Same drug + different frequency values

---

#### 3. Incomplete Data

**Condition:** Missing dosage OR missing frequency

```
Dosage = null
→ flagged
```

---

#### 4. Duplicate Entry

**Condition:** Same medication repeated within the same source

---

#### 5. Stopped vs Active Conflict

**Condition:**
```
One source → stopped
Another   → active
```

---

#### 6. Blacklisted Combinations

Static JSON rules define unsafe combinations:

```json
["aspirin", "ibuprofen"]
```

If both appear → `HIGH` severity conflict

---

### 5. Conflict Object Structure

Each conflict stores:
- `type`
- `severity`
- Conflicting values
- Involved sources
- Timestamp
- Resolution metadata

---

## Versioning (Longitudinal Tracking)

Instead of overwriting data, the system stores:

```python
versions = [
  snapshot_1,
  snapshot_2,
  ...
]
```

**When is a new version created?**

Every reconciliation request creates a new version.

**Why this design?**
- Enables full audit trail
- Supports time-based analysis
- Avoids destructive updates

**Snapshot contains:**
- Unified medications
- Detected conflicts
- Timestamp
- Action (`created` / `updated`)

---

## Conflict Resolution Logic

When resolving a conflict:

**Input:**

```json
{
  "field": "dosage",
  "corrected_value": "500mg",
  "reason": "Doctor confirmed"
}
```

**System actions:**
1. Locate conflict by ID
2. Update:
   - `status` → `resolved`
   - `resolved_at`
   - `resolution_reason`
   - `corrected_field`
   - `corrected_value`

---

**Important: Unified List Update**

The system propagates the correction:

- If `field = dosage` → update dosage in unified meds
- If `field = frequency` → update frequency
- If `field = name` → rename drug

**Result:**
- Conflict is resolved
- Unified medication reflects correction
- Full audit preserved

---

## Multi-Clinic Support

Each reconciliation includes:

```json
"clinic_id": "clinic_a"
```

**Purpose:**
- Enables clinic-level analytics
- Supports multi-tenant environments

---

## Reporting & Aggregation Logic

All aggregations operate on the **latest version only**.

---

### 1. Patients with Conflicts

Steps:
1. Extract latest version
2. Count unresolved conflicts
3. Filter >= 1
4. Group by patient

---

### 2. Conflict Summary (Time-based)

Steps:
1. Extract latest version timestamp
2. Filter by time window (e.g., 30 days)
3. Count conflicts per patient
4. Group by clinic

---

## Robustness & Input Handling

The system is designed to handle noisy real-world data.

**Handles:**
- Typos in drug names
- Mixed units (`mg`/`g`)
- Multiple frequency formats
- Missing fields
- Duplicate entries

**Validation Strategy:**

| Input Issue | Handling |
|---|---|
| Missing name | Skipped |
| Invalid dosage | Treated as incomplete |
| Unknown frequency | Normalized or flagged |
| Invalid source | Rejected (schema validation) |

## Data Model

### Collection: `reconciliations`

The core document structure is derived from the `ReconcileRequest` and versioned reconciliation output.

#### ReconcileRequest (Ingestion Schema)

| Field | Type | Description |
|---|---|---|
| `patient_id` | `string` | Unique patient identifier |
| `clinic_id` | `string \| null` | Clinic identifier (default: `"default"`) |
| `sources` | `array<array<Medication>>` | Grouped medication lists per source |

#### MedicationBase (Per Medication Entry)

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Medication name |
| `dosage` | `string \| null` | Dosage value (e.g., `"500mg"`) |
| `frequency` | `string \| null` | Frequency value (e.g., `"once daily"`) |
| `source` | `string` | Origin source label (e.g., `"EMR"`, `"patient"`) |

#### ResolveRequest (Conflict Resolution Schema)

| Field | Type | Description |
|---|---|---|
| `field` | `enum` | Field to correct — one of `"name"`, `"dosage"`, `"frequency"` |
| `corrected_value` | `string` | The corrected value to apply |
| `reason` | `string` | Audit reason for the resolution |

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

## API Endpoints

### Health

**`GET /api/v1/health/`**
Returns service health status.

---

### Medications

**`POST /api/v1/medications/`**
Create a new medication entry for a patient.

Request body: `MedicationCreate`

| Field | Type | Required |
|---|---|---|
| `name` | `string` | Yes |
| `source` | `string` | Yes |
| `patient_id` | `string` | Yes |
| `dosage` | `string \| null` | No |
| `frequency` | `string \| null` | No |

**`GET /api/v1/medications/{patient_id}`**
Fetch all medications for a given patient.

---

### Reconciliation

**`POST /api/v1/reconcile/`**
Ingest and reconcile medications from multiple sources.

Request body: `ReconcileRequest`

| Field | Type | Required |
|---|---|---|
| `patient_id` | `string` | Yes |
| `sources` | `array<array<MedicationBase>>` | Yes |
| `clinic_id` | `string \| null` | No (default: `"default"`) |

**`GET /api/v1/reconcile/{patient_id}`**
Fetch full reconciliation history (with versions) for a patient.

**`PATCH /api/v1/reconcile/resolve/{reconciliation_id}/{conflict_id}`**
Resolve a specific conflict within a reconciliation.

Request body: `ResolveRequest`
```json
{
  "field": "dosage",
  "corrected_value": "500mg",
  "reason": "Doctor confirmed"
}
```

| Field | Type | Values |
|---|---|---|
| `field` | `enum` | `"name"`, `"dosage"`, `"frequency"` |
| `corrected_value` | `string` | The corrected value to apply |
| `reason` | `string` | Audit reason for the resolution |

---

### Reports

**`GET /api/v1/reports/conflicts`**
Get a global conflict report across all patients.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `min_conflicts` | `integer` | `1` | Minimum conflict count filter |
| `days` | `integer \| null` | — | Lookback window in days |

**`GET /api/v1/reports/clinic/{clinic_id}/patients-with-conflicts`**
List all patients with unresolved conflicts for a given clinic.

**`GET /api/v1/reports/clinic/conflict-summary`**
Aggregated conflict summary across clinics within a time window.

| Query Param | Type | Default |
|---|---|---|
| `days` | `integer` | `30` |
| `min_conflicts` | `integer` | `2` |

---

### Patients

**`GET /api/v1/patients/`**
List all patients with pagination and sorting.

| Query Param | Type | Default | Constraints |
|---|---|---|---|
| `limit` | `integer` | `10` | 1–100 |
| `skip` | `integer` | `0` | >= 0 |
| `sort_by` | `string` | `"last_updated"` | — |

**`GET /api/v1/patients/{patient_id}`**
Fetch details for a specific patient.

**`GET /api/v1/patients/{patient_id}/timeline`**
Fetch the full versioned medication timeline for a patient.

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
git clone https://github.com/nav-jk/Medication-Reconciliation-Conflict-Reporting-Service.git
cd Medication-Reconciliation-Conflict-Reporting-Service

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
   - Admin/user can resolve conflict with valid reason and new corrected value.

2. **Versioning over mutation**
   - Every reconciliation creates a new snapshot
   - Enables full history tracking

3. **Denormalized structure**
   - Faster reads for aggregation
   - Trade-off: duplication across versions

4. **Static conflict rules**
   - JSON-based rules instead of external drug DB
   - Keeps system simple and deterministic
   - Possible future enhancement of using a standardised ruleset.

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

A basic UI was built using AI for demo purpose.
Demo Video can be found here []


## Final Note

This system is designed with real-world healthcare data challenges in mind:
- inconsistent inputs
- lack of ground truth
- need for auditability

The focus was on **clarity**, **extensibility**, and **robustness**, rather than over-engineering.