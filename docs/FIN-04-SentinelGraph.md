# FIN-04 — SentinelGraph
## Product Requirements Document

**Version:** 1.0  
**Hackathon scope:** 24-hour working prototype  
**Problem statement:** Financial Crime & Insider Risk Intelligence Platform

## 1. Product summary

SentinelGraph is an evidence-first investigation platform that connects employees, access privileges, customer profiles, accounts, and transactions to surface suspicious relationships between insider misuse and financial crime.

It is not an automatic accusation system. It is a **human-in-the-loop triage and investigation workbench** that explains why an alert was raised, shows the supporting event chain, compares activity with peer/role baselines, and allows an analyst to assign and resolve a case.

## 2. Problem

Fraud monitoring and employee-access monitoring are often reviewed separately. This creates blind spots:

- a privileged employee may access a customer record and then modify a beneficiary;
- multiple small transfers may form a circular or threshold-avoidance pattern;
- an account may be handled by an employee outside the employee’s normal branch or role scope;
- high-volume legitimate operations may be incorrectly treated as suspicious;
- investigators receive a score without a concise evidence trail.

## 3. Product goals

1. Correlate employee activity and financial events on one time-aware graph.
2. Detect at least three suspicious patterns with deterministic, explainable rules.
3. Display evidence beside every alert, not hidden behind an opaque score.
4. Demonstrate legitimate high-volume activity that does not generate a false positive.
5. Support case assignment, status changes, notes, and evidence export.
6. Make data provenance, timestamps, and confidence visible.

## 4. Non-goals

- Production AML compliance certification.
- Real bank integration or real customer data.
- Automatic account blocking, employee disciplinary action, or law-enforcement filing.
- Legal conclusion that a person committed fraud.
- Universal machine-learning anomaly detection.
- Identity verification or biometric monitoring.

## 5. Primary users

### Investigator / analyst
Needs a prioritized alert queue, evidence chain, graph exploration, and case workflow.

### Supervisor
Needs workload assignment, false-positive review, rule performance, and exportable case summaries.

### System administrator
Needs synthetic data loading, role configuration, rule thresholds, and audit logs.

## 6. Core user journeys

### Journey A — Review an alert
1. Analyst opens the alert queue.
2. Alerts are ranked by risk and evidence strength.
3. Analyst opens one alert.
4. System shows a plain-language explanation, rule triggers, event timeline, graph path, peer baseline, and confidence.
5. Analyst assigns the case, adds a note, and changes status to investigating or dismissed.

### Journey B — Investigate a connected pattern
1. Analyst searches employee, customer, account, transaction, or beneficiary.
2. System displays related nodes and time-bounded events.
3. Analyst expands the shortest evidence path between an employee and suspicious transactions.
4. Analyst exports a case bundle containing events, timestamps, rule results, and analyst notes.

### Journey C — Prove a legitimate high-volume scenario
1. Synthetic batch operator retrieves many records during month-end processing.
2. The volume is high but is within role, time, branch, and peer baseline.
3. System displays “monitored — no alert” with the reason.
4. This validates false-positive resistance.

## 7. MVP requirements

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-01 | Ingest synthetic employees, roles, accounts, customers, transactions, access events, and beneficiary changes | Must | Demo dataset loads successfully and records retain timestamps/source IDs |
| FR-02 | Build a time-aware relationship graph | Must | Analyst can traverse employee → access → customer/account → transaction/beneficiary |
| FR-03 | Detect repeated failed logins or abnormal access bursts | Must | At least one access anomaly is produced with supporting events |
| FR-04 | Detect privilege-scope mismatch | Must | Access outside role/branch/customer scope creates an explainable finding |
| FR-05 | Detect transaction splitting / threshold avoidance | Must | Multiple near-threshold transfers in a configured time window are linked |
| FR-06 | Detect circular money flow | Should | A → B → C → A pattern is highlighted where present |
| FR-07 | Link insider action to downstream financial anomaly | Must | Alert contains a connected evidence path, not independent scores only |
| FR-08 | Rank risk using explainable components | Must | Score decomposes into rule contributions and confidence |
| FR-09 | Support alert assignment and case status | Must | Analyst can assign, comment, and resolve/dismiss |
| FR-10 | Export evidence bundle | Must | Downloadable JSON/Markdown/PDF-like summary includes evidence and timestamps |
| FR-11 | Show legitimate high-volume scenario | Must | Batch operator does not trigger a high-risk alert solely on volume |
| FR-12 | Maintain audit trail | Should | Rule version, analyst action, timestamp, and before/after status are logged |

## 8. Quality requirements

- Every alert has an explanation panel.
- Every event has an event time and ingestion time.
- The UI distinguishes observed data, derived relationships, rule findings, and analyst judgments.
- No alert text should state that a person is guilty.
- The demo must work offline with a seeded dataset.
- The system should load the demo dashboard in under five seconds on a laptop.

## 9. Success metrics for the hackathon

- 100% of seeded suspicious scenarios detected by at least one appropriate rule.
- 0 double-counted evidence events in exported cases.
- Legitimate batch operator produces no high-severity alert from volume alone.
- Every high-severity alert includes at least three supporting events or is explicitly marked low evidence.
- Analysts can reach an evidence-backed case from the alert queue in fewer than three clicks.

## 10. Demo scenarios

1. **Insider beneficiary manipulation:** employee accesses out-of-scope customer, changes beneficiary, then related transfer occurs.
2. **Transaction splitting:** several transfers just below a configured threshold converge on a common recipient.
3. **Circular flow:** funds move through three accounts and return to a connected beneficiary.
4. **Legitimate month-end batch:** high-volume retrieval by an authorized operations role remains below alert severity because peer and role context match.
5. **Borderline case:** one rule fires but evidence is incomplete; system recommends manual review instead of a confident conclusion.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Looks like a generic dashboard | Lead with graph-linked evidence paths and live investigation workflow |
| Too many false positives | Add role/peer baselines and legitimate scenarios |
| Opaque AI scoring | Use deterministic rules with score decomposition; use LLM only for wording |
| Synthetic data seems unrealistic | Create event sequences with plausible timestamps, roles, branches, and benign activity |
| Scope explosion | One bank, three suspicious patterns, one case workflow |

## 12. Future roadmap

- Streaming event ingestion and model monitoring.
- Federated peer baselines across branches without sharing raw records.
- Analyst feedback loop for threshold calibration.
- Privacy-preserving graph analytics.
- Explainable graph neural network as a secondary—not sole—signal.
