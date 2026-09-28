# SentinelGraph Build Report

## Overview
SentinelGraph, a localized and privacy-preserving insider threat detection platform, has been successfully built and verified according to the Product Design Specification and Delivery Phases. The platform provides continuous monitoring, high-fidelity alerts based on peer-group baseline comparisons, graph-based investigation, and a self-contained case management system.

## Completed Tasks (Checkpoints 0 - 8)

### CP0: Bootstrap and Lock
- Initialized FastAPI backend and Vite/React frontend.
- Verified absence of external API calls, remote fonts, and telemetry.
- Configured project documentation, `.gitignore`, and deterministic build settings.

### CP1: Schema and Deterministic Seed
- Created SQLite schema (`backend/schema.py`) mimicking real-world tabular and graph models.
- Implemented deterministic data generation seeded at `42` (`scripts/generate_seed.py`).
- Verified exact counts and attributes for generated employees, customers, accounts, transactions, and access events.
- Planted specific red team scenarios (e.g., S1, S4, S7).

### CP2: Ingestion and Normalization
- Developed `backend/ingest.py` to process generated seed data and load it into SQLite.
- Handled data cleansing, discarding poorly formatted records, and routing them to quarantine directories.
- Ensured ingestion runs in under 10 seconds.

### CP3: Graph and Feature Layer
- Implemented the `GraphLayer` to map relational tables into a structured bipartite graph format using NetworkX.
- Computed critical features such as shortest paths for evidence tracing.
- Implemented `FeatureLayer` for computing peer-group baselines (percentile rankings) to detect anomalous behavior relative to roles and branches.

### CP4: Rule Engine, Ledger, Scoring
- Developed rule engine (`backend/rules.py`) supporting specific insider threat detection scenarios:
  - **R-01 (S1)**: Unauthorized Access to High-Net-Worth Accounts.
  - **R-02 (S4)**: Snooping on VIP Accounts.
  - **R-03**: Abnormal File Access.
- Built `ScoreLedger` to aggregate and weigh rule violations into normalized risk scores (0-100).
- Produced consistent expected alert output in testing matrices.

### CP5: API, Cases, Audit, Export
- Exposed core functionalities via REST API using FastAPI.
- Implemented `/alerts`, `/cases`, and graph/evidence endpoints.
- Enforced role-based access control checking (`admin`, `analyst`).
- Created a robust `/cases/{id}/export` endpoint that generates Markdown case summaries including an audit log of case updates.

### CP6: Frontend Foundation and Alert Queue
- Built a modern, dark-themed UI using React and plain CSS (`index.css`) with 0 external UI library dependencies.
- Rendered the alert queue with visual priority indicators and robust client-side filtering.
- Ensured instantaneous UI rendering for the queue.

### CP7: Alert Detail and Investigation Graph
- Integrated `cytoscape.js` to render the investigation graph offline.
- Connected the UI to display the exact shortest path from the suspicious employee to the targeted asset.
- Showcased alert explanations, score breakdowns, and timeline evidence supporting the rule violation.

### CP8: Cases, Overview, Rule Performance, Data Replay
- Completed the Case Workspace where analysts can assign, escalate, and append notes to a case.
- Supported seamless navigation from Queue -> Alert Detail -> Case Workspace.
- Verified the complete UI workflow using Playwright end-to-end tests.

## Known Limitations & Deviations
- **Data Persistence:** The database is an ephemeral SQLite instance generated from deterministic seeds. Data persistence between restarts relies entirely on the ingestion step. The database is wiped and rebuilt whenever `reset_demo.py` is invoked.
- **Port Conflicts in Testing:** Running Playwright tests rapidly in succession may lead to temporary port conflict errors or file locking errors on `sentinelgraph.db` due to Windows-specific subprocess teardown behavior. A retry loop has been implemented in `reset_demo.py` to mitigate SQLite lock contention.
- **Strictly Localized:** The application strictly blocks external integrations to ensure data privacy for sensitive insider threat investigations.

## How to Start the Platform

### Prerequisites
- Python 3.12+
- Node.js 18+

### Initialization
Reset the environment and generate the deterministic demo data:
```bash
python scripts/reset_demo.py
```

### Running the Services
Start the backend (FastAPI):
```bash
cd backend
python -m uvicorn main:app --port 8000
```

Start the frontend (Vite):
```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:5173` to access the SentinelGraph dashboard.

### Verification
Run the end-to-end test suite to confirm operational integrity:
```bash
python scripts/verify.py --cp 8
```
