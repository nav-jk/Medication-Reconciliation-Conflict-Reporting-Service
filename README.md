# 🩺 Medication Reconciliation Service API

## 📌 Overview

This service provides APIs to manage patient medications, perform medication reconciliation across multiple sources, resolve conflicts, and generate reports.

It is built using **FastAPI** and follows RESTful principles.

---

## 🚀 Base URL

```
/api/v1
```

---

## 🧩 Features

* Medication management
* Patient data retrieval
* Medication reconciliation across sources
* Conflict detection & resolution
* Reporting and analytics
* Patient timeline tracking

---

## 📂 API Endpoints

---

# 🟢 Health

## 🔹 GET `/health/`

Check if the service is running.

### Response

```json
200 OK
{}
```

---

# 💊 Medications

## 🔹 POST `/medications/`

Create a new medication entry.

### Request Body

```json
{
  "name": "Paracetamol",
  "dosage": "500mg",
  "frequency": "Twice a day",
  "source": "hospital",
  "patient_id": "123"
}
```

### Required Fields

* `name`
* `source`
* `patient_id`

### Response

```json
200 OK
{}
```

---

## 🔹 GET `/medications/{patient_id}`

Fetch all medications for a patient.

### Path Params

* `patient_id` (string)

### Response

```json
200 OK
[]
```

---

# 🔄 Reconciliation

## 🔹 POST `/reconcile/`

Perform reconciliation of medications from multiple sources.

### Request Body

```json
{
  "patient_id": "123",
  "sources": [
    [
      {
        "name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "Twice a day",
        "source": "hospital"
      }
    ],
    [
      {
        "name": "Paracetamol",
        "dosage": "650mg",
        "frequency": "Once a day",
        "source": "clinic"
      }
    ]
  ]
}
```

### Notes

* `sources` is a list of medication lists from different systems
* Used to detect conflicts and unify data

### Response

```json
200 OK
{
  "unified": [],
  "conflicts": []
}
```

---

## 🔹 GET `/reconcile/{patient_id}`

Get all reconciliation records for a patient.

### Response

```json
200 OK
[]
```

---

## 🔹 PATCH `/reconcile/resolve/{reconciliation_id}/{conflict_id}`

Resolve a specific conflict.

### Path Params

* `reconciliation_id`
* `conflict_id`

### Request Body

```json
{
  "reason": "Doctor confirmed correct dosage",
  "field": "dosage",
  "corrected_value": "500mg"
}
```

### Allowed Fields

* `name`
* `dosage`
* `frequency`

### Response

```json
200 OK
{}
```

---

# 📊 Reports

## 🔹 GET `/reports/conflicts`

Retrieve conflict statistics.

### Query Params

| Param         | Type | Default  | Description                 |
| ------------- | ---- | -------- | --------------------------- |
| min_conflicts | int  | 1        | Minimum conflicts to filter |
| days          | int  | optional | Filter by last N days       |

### Example

```
/reports/conflicts?min_conflicts=2&days=7
```

### Response

```json
200 OK
[]
```

---

# 👤 Patients

## 🔹 GET `/patients/`

List patients with pagination and sorting.

### Query Params

| Param   | Type   | Default      | Description        |
| ------- | ------ | ------------ | ------------------ |
| limit   | int    | 10           | Max results (≤100) |
| skip    | int    | 0            | Offset             |
| sort_by | string | last_updated | Sorting field      |

### Response

```json
200 OK
[]
```

---

## 🔹 GET `/patients/{patient_id}`

Get details of a specific patient.

### Response

```json
200 OK
{}
```

---

## 🔹 GET `/patients/{patient_id}/timeline`

Get full patient medication history timeline.

### Description

Returns:

* Medication changes
* Reconciliation events
* Conflict resolutions
* Timestamps for each action

### Response

```json
200 OK
[
  {
    "event": "medication_added",
    "timestamp": "2026-03-20T10:00:00Z"
  }
]
```

---

# 🏠 Root

## 🔹 GET `/`

Basic root endpoint.

### Response

```json
200 OK
{}
```

---

# 📦 Data Models

## MedicationBase

```json
{
  "name": "string",
  "dosage": "string | null",
  "frequency": "string | null",
  "source": "string"
}
```

---

## MedicationCreate

```json
{
  "name": "string",
  "dosage": "string | null",
  "frequency": "string | null",
  "source": "string",
  "patient_id": "string"
}
```

---

## ReconcileRequest

```json
{
  "patient_id": "string",
  "sources": [[MedicationBase]]
}
```

---

## ResolveRequest

```json
{
  "reason": "string",
  "field": "name | dosage | frequency",
  "corrected_value": "string"
}
```

---

## ValidationError

Standard FastAPI validation error format.

---

# ⚠️ Error Handling

## 422 Validation Error

Returned when request body or parameters are invalid.

```json
{
  "detail": [
    {
      "loc": ["body", "field"],
      "msg": "error message",
      "type": "type_error"
    }
  ]
}
```

---

# 🧠 Key Concepts

## Medication Reconciliation

Process of:

* Merging medication lists from multiple sources
* Detecting inconsistencies
* Producing a unified list
* Flagging conflicts

## Conflict Resolution

* Manual correction of mismatched fields
* Maintains audit trail
* Updates unified dataset

## Timeline Tracking

* Tracks all changes over time
* Enables auditability and debugging
* Useful for clinical history analysis

---

# 🛠️ Suggested Improvements (Optional but Recommended)

* Add authentication (JWT)
* Add versioning for reconciliation snapshots
* Store audit logs for compliance
* Add role-based access control
* Improve response schemas (currently empty)

---

# 📌 Summary

This API provides a complete backend for:

* Managing patient medications
* Detecting inconsistencies across systems
* Resolving conflicts safely
* Tracking full medication history

---

If you want, I can next:

* Generate **Postman collection**
* Write **DB schema (Mongo)**
* Add **sample responses for each endpoint (realistic)**
* Or help you design **timeline storage properly (important for your assignment)**
