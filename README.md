# DealerOS – Data Reconciliation Dashboard

## Project Overview

DealerOS is a data reconciliation application that compares records from two independent systems (System A and System B). It identifies missing records, duplicate entries, orphan records, and mismatches in values, locations, and dates.

The application uses Django REST Framework for the backend, SQLite for data storage, and React for the frontend.

## Technology Stack

- **Frontend:** React, JavaScript, CSS
- **Backend:** Python, Django, Django REST Framework
- **Database:** SQLite
- **Data Source:** CSV files
- **Testing:** Pytest

## Features Implemented

- CSV import for Locations, System A, and System B.
- Preservation of parsed values and raw-value fields.
- Record reference normalization.
- Handling of blank values as NULL.
- Idempotent imports using `update_or_create()`.
- Reconciliation of System A and System B records.
- Detection of missing, orphan, duplicate, value, location, date, and voided-record disagreements.
- Organization-based data filtering through the backend API.
- React dashboard with organization selection and reason filters.
- Sorting and pagination of disagreement records.
- Summary cards displaying disagreement counts.

## Project Structure

```text
dealors/
├── backend/
│   ├── config/
│   ├── reconcile/
│   ├── data/
│   ├── manage.py
│   └── db.sqlite3
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── env/
└── requirement.txt
```

## Setup Instructions

### 1. Backend Setup

Open a terminal in the backend directory.

Activate the virtual environment if it is not already active:

```powershell
..\env\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r ../requirement.txt
```

Run database migrations:

```bash
python manage.py migrate
```

Import CSV data:

```bash
python manage.py import_data
```

Start the backend server:

```bash
python manage.py runserver
```

Backend URL: `http://127.0.0.1:8000/`

### 2. Frontend Setup

Open another terminal in the frontend directory.

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Frontend URL: `http://localhost:5173/`

## Testing

Run the backend tests from the backend directory:

```bash
pytest -v
```

The current test run completed with 14 passing tests.

## Data Import Verification

The CSV importer was run twice.

| Dataset | Expected Records |
|---|---:|
| Locations | 5 |
| System A | 120 |
| System B | 121 |

The second import completed with zero reported errors. Database counts should remain unchanged after repeated imports.

## AI Assistance

AI assistance was used during development for debugging, code explanations, test-case development, and frontend implementation. The implementation and behavior were reviewed and tested during development.

### 1. One actual AI mistake and how it was caught

AI initially suggested that a clean matching record should appear in the API response. A test exposed the incorrect expectation. I reviewed the reconciliation behavior and corrected the test because matching records should not be returned as disagreements.

### 2. Least confident part

The most challenging part is handling tenant isolation when System A and System B reference different organization locations. I need to be particularly careful that records belonging to another organization are not exposed through the API.

### 3. What I would improve with a second day

I would improve importer error handling and raw CSV preservation, add more edge-case tests for tenant isolation and malformed records, and improve the documentation.

## Limitations / Future Improvements

- Authentication and role-based access control are not implemented.
- Production deployment is not included.
- Import error reporting and raw-data preservation can be improved.
