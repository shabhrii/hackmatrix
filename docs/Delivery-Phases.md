# SentinelGraph — Delivery Phases

## Phase 0 — Scope lock and demo narrative
**Target:** Hours 0–2

### Deliverables

- Finalize one synthetic bank scenario.
- Select the three core patterns: scope mismatch, insider action linked to transaction, and transaction splitting/circular flow.
- Define one legitimate high-volume scenario.
- Freeze schema, thresholds, and screen list.

### Exit criteria

The team can describe the complete demo in three minutes without adding new features.

## Phase 1 — Synthetic data and schema
**Target:** Hours 2–5

### Deliverables

- Seed employees, roles, branches, customers, accounts, beneficiaries, transactions, logins, access events, and profile changes.
- Create suspicious and legitimate event sequences.
- Add timestamps, source IDs, and scenario labels.
- Implement resettable deterministic seed.

### Exit criteria

A clean database can be rebuilt from one command and contains at least five scenarios.

## Phase 2 — Ingestion and normalization
**Target:** Hours 4–7

### Deliverables

- CSV/JSON loader.
- Required-field validation.
- Timestamp normalization.
- Entity-reference validation.
- Raw-event provenance.

### Exit criteria

Invalid records are reported without crashing the pipeline; valid records are queryable.

## Phase 3 — Graph and feature layer
**Target:** Hours 6–10

### Deliverables

- Build adjacency structures and event relationships.
- Implement employee/account/customer traversal.
- Compute peer and role baselines.
- Build money-flow paths and event timelines.

### Exit criteria

Given an employee or transaction, the system returns connected entities and ordered evidence events.

## Phase 4 — Explainable rule engine
**Target:** Hours 8–12

### Deliverables

- Implement R-03, R-04, R-05, and R-06 first.
- Add R-02 peer-baseline protection.
- Return structured findings with evidence IDs.
- Add severity/confidence calculation.
- Add unit tests for suspicious and benign scenarios.

### Exit criteria

All core seeded suspicious scenarios trigger the intended rules, and the legitimate batch scenario does not become high severity.

## Phase 5 — Case management API
**Target:** Hours 10–14

### Deliverables

- Alert list/filter endpoint.
- Alert detail endpoint.
- Case assignment and status changes.
- Notes and audit log.
- Evidence export.

### Exit criteria

An analyst can move from alert → evidence → case assignment → export without database edits.

## Phase 6 — Investigation dashboard
**Target:** Hours 12–17

### Deliverables

1. Alert queue with severity, confidence, rule labels, and status.
2. Alert detail with plain-language explanation.
3. Event timeline.
4. Interactive relationship graph.
5. Evidence drawer.
6. Case panel and export action.
7. “Why not an alert?” legitimate activity panel.

### Exit criteria

A judge can understand an alert without developer narration.

## Phase 7 — Validation and demo hardening
**Target:** Hours 16–20

### Deliverables

- Add contradictory/borderline case.
- Verify evidence IDs are not duplicated.
- Verify filters and reset flow.
- Test missing timestamps and small peer groups.
- Confirm masked identifiers.
- Prepare backup screenshots/video.

### Exit criteria

The system handles expected failure cases honestly and can recover from a demo reset.

## Phase 8 — Pitch and rehearsal
**Target:** Hours 20–24

### Final demo sequence

1. Open alert queue.
2. Select insider-linked transaction alert.
3. Show evidence chain and graph.
4. Expand rule contribution and peer baseline.
5. Assign case and add analyst note.
6. Show threshold-splitting scenario.
7. Show legitimate batch activity with no high alert.
8. Export evidence bundle.
9. State limitations and next steps.

## Priority cuts if time is lost

### Keep at all costs

- synthetic data reset;
- R-03/R-04/R-05;
- evidence panel;
- timeline;
- alert queue;
- legitimate scenario;
- case assignment.

### Cut first

- real-time streaming;
- graph database migration;
- machine-learning model;
- PDF export styling;
- advanced authentication;
- multiple bank/branch tenants;
- mobile UI.

## Definition of done

The prototype is done when:

- a suspicious sequence is detected;
- the alert is linked to exact evidence;
- an analyst can investigate and assign it;
- a legitimate high-volume sequence is handled appropriately;
- at least one borderline case is marked for review;
- the team can explain every number shown on screen.
