# SentinelGraph — Detection Rules

## 1. Rule-engine contract

Every rule must return:

- `rule_id` and version;
- status: `triggered`, `not_triggered`, or `insufficient_evidence`;
- severity and confidence;
- the exact evidence event IDs;
- derived facts and thresholds;
- a human-readable explanation generated from those facts;
- recommended analyst action.

Rules should be independently testable and should not mutate raw events.

## 2. Severity model

| Severity | Meaning | Prototype action |
|---|---|---|
| Critical | Multiple connected high-confidence indicators | Immediate supervisor review |
| High | Strong evidence chain with at least two independent indicators | Create investigation case |
| Medium | One meaningful anomaly or incomplete connection | Queue for analyst review |
| Low | Contextual signal only | Monitor; do not escalate alone |
| Informational | Legitimate or expected activity with audit value | No alert |

## 3. Core rules

### R-01 — Repeated failed authentication

**Purpose:** Detect credential attack or account misuse signals.

**Trigger:** At least `N=5` failed login events for one employee within `15 minutes`, or failed logins from at least two distinct device/IP hashes followed by a success within `30 minutes`.

**Evidence:** failed login IDs, successful login ID if applicable, device/IP diversity, time span.

**Suppressions:** Known training environment or explicitly configured security test account.

**Output explanation:**

> Employee E17 had 7 failed login attempts across 2 devices in 11 minutes, followed by a successful login from a new device.

**Caution:** This is an access signal, not proof of compromise.

### R-02 — Excessive record retrieval

**Purpose:** Detect unusually large access volume.

**Trigger:** Employee retrieves more than `P99` of peer volume for the same role and shift, or more than an absolute threshold such as `50` distinct customer records within `10 minutes`.

**Required context:** role, branch, action type, peer population, batch/job identifier.

**False-positive control:** If the employee is part of a known month-end batch and volume is within the batch operator baseline, emit `informational` or no alert.

### R-03 — Role or branch scope mismatch

**Purpose:** Detect access outside authorized scope.

**Trigger:** Employee accesses a customer/account outside their role permission set, assigned branch, or approved case assignment.

**Evidence:** employee role, permission rule, target branch, access event, authorization state.

**Severity:** Medium alone; High when followed by profile or beneficiary change.

### R-04 — Beneficiary/profile change followed by financial action

**Purpose:** Connect insider activity to a downstream financial event.

**Trigger:** Within `60 minutes` of an out-of-scope access or profile/beneficiary change, a transaction is initiated from the affected account to a new or recently modified destination.

**Evidence:** access event, change event, transaction, destination novelty, elapsed minutes.

**Severity:** High when two or more independent conditions are satisfied.

**Explanation template:**

> An out-of-scope access and beneficiary change preceded a transfer to a new destination by 11 minutes. This finding is based on events A-19, P-07, and T-88.

### R-05 — Transaction splitting / threshold avoidance

**Purpose:** Detect multiple transfers designed to avoid an attention threshold.

**Trigger:** At least `3` transfers from the same source or connected source accounts to the same destination within `24 hours`, where each amount is between `70%` and `99%` of the configured threshold and the aggregate exceeds it.

**Evidence:** all transaction IDs, threshold, aggregate, time window, common destination.

**Controls:** Exclude scheduled salary, utility, or known batch payments when tagged as recurring and matched to the account’s normal pattern.

### R-06 — Circular money flow

**Purpose:** Detect funds moving through intermediaries and returning to a connected account.

**Trigger:** A directed cycle of length 3–5 occurs within `72 hours`, with aggregate amounts above a configured minimum and at least one account sharing an owner, beneficiary, employee relationship, or recent profile change.

**Evidence:** ordered transaction path, timestamps, amounts, relationship link.

**Severity:** Medium if only a cycle exists; High if paired with R-03 or R-04.

### R-07 — Peer-baseline anomaly

**Purpose:** Compare activity with role- and context-matched peers.

**Features:** access count, distinct customers, after-hours ratio, beneficiary edits, transaction-related actions, and branch deviation.

**Trigger:** Robust z-score or percentile beyond configured threshold, such as `P99`, but only when the peer group has a minimum size of 5.

**Insufficient evidence:** If peer group is too small, do not compute a confident baseline.

### R-08 — After-hours privileged action

**Purpose:** Detect sensitive activity outside expected hours.

**Trigger:** Privileged action occurs outside the employee’s normal shift and is not associated with an approved on-call schedule.

**Severity:** Low or Medium alone; increases when linked to R-04.

## 4. Alert aggregation logic

Do not simply add every rule score. Aggregate findings when they share:

- employee ID;
- affected account/customer;
- destination account;
- time window of 24–72 hours.

Increase severity when independent evidence types connect:

```text
access anomaly + profile change + financial movement = connected alert
```

Keep a finding ledger to prevent duplicate events from being counted twice.

## 5. Legitimate scenarios that must not alert strongly

1. Month-end operations batch with high retrieval volume, expected role, expected time, and approved job ID.
2. Customer-service employee accessing a customer after a valid case assignment.
3. On-call security administrator performing after-hours access with approved ticket.
4. Recurring salary disbursement with known batch signature.

## 6. Manual-review triggers

Produce `insufficient_evidence` when:

- the peer group has fewer than five comparable employees;
- timestamps conflict or are missing;
- entity resolution is ambiguous;
- a transaction path depends on an unverified account relationship;
- a threshold is crossed but the destination is a known recurring payment.

## 7. Rule testing matrix

| Scenario | Expected result |
|---|---|
| 7 failed logins, then new-device success | R-01 triggered |
| 80 normal batch retrievals by batch role | R-02 informational/no high alert |
| Teller accesses unrelated branch customer | R-03 triggered |
| Out-of-scope access + beneficiary change + transfer | R-04 high |
| Four near-threshold transfers to one destination | R-05 triggered |
| A→B→C→A within 72 hours | R-06 triggered |
| Small peer group | R-07 insufficient evidence |
| Approved on-call admin access | R-08 suppressed or low |
| Single unusual event with no connection | Medium/low, not critical |

## 8. Explainability requirements

Every alert must answer:

1. What happened?
2. Which rule fired?
3. Which exact events support it?
4. Why is this unusual in context?
5. What information is missing?
6. What should the analyst inspect next?

Avoid text such as “AI detected fraud.” Use “The system identified a pattern requiring review.”
