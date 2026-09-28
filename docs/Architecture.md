# SentinelGraph — Architecture

## 1. Architecture principles

1. **Evidence before score:** alerts are assembled from events, relationships, and rules.
2. **Deterministic core:** the prototype’s numeric results must be reproducible.
3. **Time-aware graph:** relationships and access rights can change over time.
4. **Human decision boundary:** the system prioritizes investigation; it does not declare guilt.
5. **Separation of concerns:** raw events, derived features, rule findings, and analyst decisions are stored separately.
6. **Synthetic-data first:** no production customer or employee data is required.

## 2. Logical architecture

```text
Synthetic CSV/JSON feeds
        |
        v
Ingestion + validation + provenance
        |
        +--> Raw event store
        |
        v
Normalization / entity resolution
        |
        +--> Employees, roles, customers, accounts, beneficiaries
        +--> Access events, transactions, profile changes
        |
        v
Feature builder + temporal graph builder
        |
        +--> Peer/role baselines
        +--> Money-flow edges
        +--> Access-scope relationships
        |
        v
Explainable rule engine
        |
        +--> Findings with evidence IDs
        +--> Alert aggregation + confidence
        |
        v
Case management API
        |
        +--> Alert queue
        +--> Graph/timeline investigation
        +--> Assignment/status/notes
        +--> Evidence export
        |
        v
Web dashboard
```

## 3. Suggested implementation stack

### Fastest hackathon option

- **Frontend:** React + TypeScript + Tailwind or a simple component library.
- **Backend:** Python FastAPI.
- **Data store:** SQLite for portability; NetworkX for graph traversal.
- **Optimization/analytics:** pandas and standard Python; optional scikit-learn for peer anomaly features.
- **Charts/graph:** React Flow, Cytoscape.js, or D3.
- **Export:** JSON plus Markdown/HTML case report.

A graph database is optional. SQLite plus an adjacency table is easier to stabilize in 24 hours. Use Neo4j only if the team already knows it.

## 4. Data model

### Core entities

- `employees(employee_id, name, role_id, branch_id, manager_id, active_from, active_to)`
- `roles(role_id, name, permission_set)`
- `customers(customer_id, segment, branch_id, risk_band)`
- `accounts(account_id, customer_id, account_type, opened_at, status)`
- `beneficiaries(beneficiary_id, account_id, destination_account, created_at, created_by)`
- `transactions(txn_id, source_account, destination_account, amount, currency, timestamp, channel, status)`
- `access_events(event_id, employee_id, customer_id, account_id, action, timestamp, result, device_id, ip_hash)`
- `profile_changes(change_id, employee_id, customer_id, field, old_value_hash, new_value_hash, timestamp)`
- `login_events(event_id, employee_id, timestamp, result, device_id, ip_hash)`
- `findings(finding_id, rule_id, severity, confidence, created_at, status)`
- `finding_evidence(finding_id, event_id, relationship_type)`
- `cases(case_id, owner_id, status, created_at, updated_at)`
- `case_notes(note_id, case_id, author_id, body, created_at)`
- `audit_log(audit_id, actor_id, action, target_type, target_id, timestamp, metadata_json)`

### Important distinction

Each record should retain:

- `event_time`: when the business activity occurred;
- `ingested_at`: when the platform received it;
- `source_id`: originating feed or file;
- `rule_version`: version used for derived findings.

## 5. Graph model

### Node types

`Employee`, `Role`, `Branch`, `Customer`, `Account`, `Beneficiary`, `Transaction`, `Device`, `Case`.

### Edge types

- `EMPLOYEE_HAS_ROLE`
- `EMPLOYEE_ASSIGNED_TO_BRANCH`
- `EMPLOYEE_ACCESSED_CUSTOMER`
- `EMPLOYEE_CHANGED_PROFILE`
- `EMPLOYEE_CHANGED_BENEFICIARY`
- `CUSTOMER_OWNS_ACCOUNT`
- `ACCOUNT_SENT_TO_ACCOUNT`
- `TRANSACTION_PART_OF_PATTERN`
- `EMPLOYEE_USED_DEVICE`

Every edge should have `timestamp`, `source_event_id`, and optional `confidence`.

## 6. Processing pipeline

### Step 1 — Validate
Reject or quarantine events with missing IDs, invalid timestamps, negative amounts, or unknown entities.

### Step 2 — Normalize
Convert timestamps to UTC internally, normalize currency and action names, and hash sensitive demo identifiers when displayed.

### Step 3 — Build features
Compute:

- access volume by employee, role, branch, and time window;
- peer median and percentile;
- out-of-scope access count;
- near-threshold transaction count;
- common destination concentration;
- time from access/profile change to transaction;
- path length and cycle membership.

### Step 4 — Run rules
Rules return structured findings, not prose:

```json
{
  "rule_id": "R-04",
  "severity": "high",
  "confidence": 0.87,
  "evidence_event_ids": ["A-19", "P-07", "T-88"],
  "explanation_facts": {
    "scope_violation": true,
    "minutes_to_transfer": 11,
    "peer_percentile": 99
  }
}
```

### Step 5 — Aggregate alerts
Group findings that share an employee, account, customer, or time window. Preserve individual findings so analysts can inspect the score composition.

## 7. Risk scoring

Use a transparent weighted model:

```text
risk_score = min(100,
  25 * high_severity_rules
+ 15 * medium_severity_rules
+ 20 * connected_financial_action
+ 15 * peer_baseline_extremeness
+ 10 * evidence_independence
+ 10 * temporal_proximity
+  5 * repeat_pattern
)
```

This is a prototype score, not a regulatory model. The UI must show the components and the evidence count.

## 8. API surface

- `POST /demo/reset`
- `GET /alerts?status=&severity=`
- `GET /alerts/{id}`
- `GET /alerts/{id}/evidence`
- `GET /graph?entity_type=&entity_id=&from=&to=`
- `GET /timeline?entity_id=&from=&to=`
- `POST /cases`
- `PATCH /cases/{id}`
- `POST /cases/{id}/notes`
- `GET /cases/{id}/export`
- `GET /metrics/rule-performance`

## 9. Security and privacy for the prototype

- Use seeded demo credentials and role-based UI/API permissions.
- Mask account numbers and hash IP/device values in the UI.
- Keep customer identity separate from investigation evidence where possible.
- Log every analyst action.
- Do not send raw financial records to an external LLM.

## 10. Failure handling

- If entity resolution is ambiguous, create an `UNRESOLVED_ENTITY` warning.
- If event time is missing, exclude it from temporal rules and flag it.
- If a graph path depends on stale data, display the staleness.
- If a rule has insufficient evidence, produce `manual_review` rather than high severity.
- If the optimizer/rule engine fails, retain the last successful version and show processing status.
