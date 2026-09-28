# SentinelGraph — Product Design Specification

## 1. Design direction

SentinelGraph should feel like a **calm investigation console**, not a dramatic fraud-detection dashboard. The design must communicate scrutiny, evidence, and analyst control.

### Design principles

- Evidence is always one click away.
- Red is reserved for risk, not decoration.
- A score never appears without its components.
- Observed events, derived findings, and analyst decisions look different.
- The interface shows uncertainty rather than hiding it.
- Dense information is organized into progressive disclosure.

## 2. Visual language

### Palette

- Background: deep navy/charcoal for the investigation workspace.
- Surface: slate panels with clear borders.
- Primary text: warm white.
- Secondary text: muted blue-gray.
- Critical: restrained red.
- High: amber/orange.
- Medium: blue.
- Informational: green.
- Derived/AI-assisted text: violet accent, never used as a risk color.

Use color plus labels/icons so severity is not color-dependent.

### Typography

- Use a readable sans-serif for the interface.
- Use a monospaced font for IDs, timestamps, rule IDs, and event references.
- Keep alert titles in sentence case.
- Use short labels: `High · R-04`, `Evidence 3`, `Manual review`.

## 3. Primary navigation

Left navigation:

1. **Overview**
2. **Alert queue**
3. **Investigation graph**
4. **Cases**
5. **Rule performance**
6. **Data replay**

Top bar:

- current demo tenant;
- replay/live indicator;
- data freshness status;
- analyst identity;
- reset demo control.

## 4. Screen specifications

### Screen A — Overview

Purpose: orient the analyst in under ten seconds.

Components:

- open high/medium alerts;
- alerts by rule;
- median evidence count;
- false-positive test status;
- last ingestion time;
- compact “active investigation” list.

Avoid vanity metrics such as “AI accuracy” unless the test set is visible.

### Screen B — Alert queue

Table columns:

| Column | Content |
|---|---|
| Severity | High/medium/low label and icon |
| Alert | Plain-language title |
| Subject | Employee/account/customer masked ID |
| Rules | R-03, R-04, R-05 chips |
| Evidence | Count and independence indicator |
| Confidence | Percentage plus confidence label |
| Age | Time since event/alert |
| Owner | Assigned analyst |
| Status | New, investigating, dismissed, escalated |

Filters:

- severity;
- rule;
- status;
- employee/branch;
- time range;
- evidence completeness.

### Screen C — Alert detail

Layout:

```text
Header: severity + alert title + status + owner

Left 65%: evidence timeline and graph
Right 35%: explanation, score breakdown, actions

Bottom: evidence table, notes, audit history
```

Header example:

> **High — Insider-linked beneficiary change**  
> Requires investigation · Confidence 87% · 3 independent evidence events

Explanation card:

- **What happened:** concise statement.
- **Why it matters:** connection to financial event.
- **Evidence:** event IDs and timestamps.
- **What is missing:** unresolved facts.
- **Recommended next step:** inspect beneficiary history and related accounts.

Score breakdown must show:

- scope mismatch: +25;
- beneficiary change: +20;
- transfer within 60 minutes: +20;
- peer abnormality: +15;
- evidence independence: +7;
- total: 87/100.

### Screen D — Investigation graph

Node styling:

- Employee: indigo square;
- Customer: teal circle;
- Account: blue circle;
- Transaction: amber diamond;
- Beneficiary: purple hexagon;
- Finding: red outlined halo.

Edge styling:

- access: thin blue;
- profile/beneficiary change: orange;
- money movement: thick green/amber directional edge;
- rule-supported relationship: animated or highlighted only on selection.

Interaction:

- hover shows event metadata;
- click pins evidence in the side panel;
- drag to arrange;
- time slider filters edges;
- “shortest evidence path” button highlights the minimum chain connecting subject to transaction.

### Screen E — Legitimate activity explanation

This screen is essential for differentiation.

Display:

> **Monitored — no high-severity alert**  
> High retrieval volume matched the employee’s batch-operator role, approved job ID, expected shift, and peer baseline.

Show the same evidence style as suspicious alerts. The system must explain not only why it alerted, but also why it did not escalate.

### Screen F — Case workspace

Components:

- case title and status;
- assigned analyst;
- evidence checklist;
- analyst notes;
- related alerts;
- next action;
- export evidence button;
- immutable activity log.

## 5. Interaction behavior

- Clicking an alert should preserve queue filters when the analyst returns.
- Any status change requires an optional reason and always writes an audit entry.
- “Dismiss” should require a reason such as legitimate batch, approved access, duplicate, or insufficient evidence.
- “Escalate” should show the evidence bundle preview before export.
- Long IDs should be copyable, but masked by default.
- Every graph selection should have a keyboard-accessible equivalent in the evidence list.

## 6. Content and tone

Use language that is precise and non-accusatory:

| Avoid | Use instead |
|---|---|
| Fraudster detected | Pattern requiring investigation |
| Employee committed fraud | Activity is inconsistent with expected scope |
| AI confirms guilt | Rules found connected anomalies |
| 99% certain fraud | 99% evidence confidence for this rule pattern |
| Clean employee | No high-severity pattern detected in the selected data |

## 7. Empty, error, and uncertainty states

### No evidence

> No connected evidence was found within the selected time window. This alert should not be escalated without additional information.

### Small peer group

> Peer comparison unavailable: only 3 comparable employees. The system has not used peer-baseline evidence in this score.

### Stale data

> Last source update: 47 minutes ago. Availability of recent events may be incomplete.

### Ambiguous identity

> Two possible account matches found. This relationship is excluded from the high-confidence path until resolved.

## 8. Demo visual hierarchy

The judge should see this sequence visually:

1. suspicious event;
2. connected graph path;
3. supporting timeline;
4. rule explanation;
5. legitimate comparison;
6. analyst action;
7. evidence export.

Do not lead with a chatbot. If an assistant is included, place it as an optional “Ask about this evidence” panel that can answer only from the selected evidence set.

## 9. Accessibility and trust

- Keyboard navigation for queue and evidence.
- Severity represented by text and icon as well as color.
- Timestamps shown in local timezone with UTC tooltip.
- Do not expose raw sensitive identifiers in screenshots.
- Include a persistent banner: **Synthetic hackathon data — not for real financial decisions.**
