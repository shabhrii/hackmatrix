# SentinelGraph: Autonomous Build Script

Paste this whole file as the first message to the agent. Before that, create an empty project folder and copy the five spec files into `docs/`:

- `docs/FIN-04-SentinelGraph.md` (PRD)
- `docs/Architecture.md`
- `docs/Delivery-Phases.md`
- `docs/Detection-Rules.md`
- `docs/Product-Design-Specification.md`

Set terminal command execution to auto-run so the agent is not blocked on approvals.

---

## 0. Your role and operating contract

You are the sole engineer building SentinelGraph, an evidence-first investigation console linking insider access events to financial transactions. The five documents in `docs/` are the specification. Read all five completely before writing any code. Where this script and the docs differ, section 3 of this script resolves the conflict; otherwise the docs win.

**Autonomy rules (non-negotiable):**

1. Do not ask me questions. Do not pause for confirmation. If something is ambiguous, pick the option most consistent with the docs, write one line to `DECISIONS.md` (date, question, choice, reason), and continue.
2. Do not stop at a failing test, a build error, a port conflict, a missing dependency or a broken UI. Debug and fix it yourself using the protocol in section 2.
3. Work strictly in checkpoint order (section 5). You may not start checkpoint N+1 until the gate for checkpoint N passes.
4. Never make a gate pass by weakening it. Do not delete tests, loosen assertions, hardcode expected outputs, skip failing cases, or special-case scenario IDs inside rule code. Fix the root cause.
5. Everything must run offline: no CDN links, no remote fonts, no external API calls, no LLM calls. Explanations are built from templates filled with derived facts.
6. Scripts must be cross-platform. Detect the OS. Prefer Python scripts and npm scripts over bash-only or PowerShell-only commands.
7. Stop only when the final checkpoint passes and `docs/BUILD_REPORT.md` is written. Then give a short summary.

---

## 1. Locked decisions

| Area | Decision |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLite (single file), NetworkX, pandas, pydantic v2, pytest |
| Frontend | React + TypeScript + Vite, React Router, Cytoscape.js for the graph, plain CSS with design tokens (no Tailwind, no component library) |
| Fonts | IBM Plex Sans and IBM Plex Mono, installed via `@fontsource` packages so they ship in the bundle |
| Verification | pytest for backend, Playwright for end-to-end and screenshots |
| Determinism | Seed value 42. Same seed must yield byte-identical database contents across runs |
| Currency and threshold | INR. Attention threshold for R-05 is 10,00,000, configurable in a `config` table |
| Time | Store UTC. Display in the browser's local timezone with a UTC tooltip |
| Auth | Three seeded demo users (analyst, supervisor, admin) with a user switcher in the top bar and a role header on the API. No real authentication |
| Optional assistant | Do not build a chatbot or LLM panel |
| Repo layout | `backend/`, `frontend/`, `data/seed/`, `docs/`, `scripts/`, `DECISIONS.md`, `DEBUG_LOG.md`, `README.md` |

One-command interface, all in `scripts/` and wired to npm/Make aliases as needed:

- `python scripts/setup.py` installs backend and frontend dependencies
- `python scripts/reset_demo.py` rebuilds the database from seed files through the real ingestion pipeline
- `python scripts/dev.py` starts backend and frontend, waits for health, prints URLs
- `python scripts/verify.py --cp N` runs the gate for checkpoint N (and every earlier gate)

Create `verify.py` at CP0 and extend it at every checkpoint.

---

## 2. Self-debug protocol

Applies to every failure, at every checkpoint.

**Loop:**

1. Run the command. Capture the full error output, not a summary.
2. Read the actual failing line and the code around it. Do not guess from the error class alone.
3. State one hypothesis in `DEBUG_LOG.md` (checkpoint, symptom, hypothesis).
4. Apply the smallest fix that addresses the root cause.
5. Re-run the failing command, then re-run the current gate.
6. If it passes, append the resolution to `DEBUG_LOG.md` and continue.

**Escalation ladder** (per issue, not per checkpoint):

- Attempts 1 to 2: targeted fix based on the error.
- Attempts 3 to 4: add logging or a minimal reproduction script, isolate the failing layer (data, rule, API, UI), and fix there. Check dependency versions, path issues, encoding, timezone handling and stale caches.
- Attempt 5: change approach. Rewrite the smallest failing unit from scratch, or swap the library (for example Cytoscape layout plugin for a simpler built-in layout).
- After attempt 5 with no fix: pick the fallback from the "cut first" list in `docs/Delivery-Phases.md`, log it in `DECISIONS.md` as a deviation with the reason, and continue. Never leave a checkpoint half-done without recording it.

**Specific traps to handle without being told:**

- Port already in use: pick the next free port, write it to a `.ports.json`, have the frontend read it.
- Windows path or line-ending issues: normalize with `pathlib`, set `.gitattributes`.
- Timezone bugs: all comparisons on UTC-aware datetimes; test one case across a date boundary.
- SQLite locking in tests: use a separate temp database per test session.
- Frontend blank screen: check browser console via Playwright, fix until there are zero console errors.
- Vite proxy or CORS failures: configure the dev proxy rather than loosening the API.
- Flaky tests: find the nondeterminism (ordering, unseeded randomness, wall-clock time) and remove it. Never retry until green.

**Regression rule:** every gate runs all earlier gates. A regression is fixed before continuing.

**Commit rule:** after each gate passes, commit and tag: `git commit -m "cpN: <plain description>"` then `git tag cpN`. Commit messages are short, lowercase, factual. No emoji, no "feat:" spam, no marketing language.

---

## 3. Spec conflicts and how to resolve them

Log each in `DECISIONS.md` at CP0.

1. **Score formula vs the alert-detail example.** `Architecture.md` gives a formula counting rules; `Product-Design-Specification.md` shows a breakdown of 25 + 20 + 20 + 15 + 7 = 87. Implement the indicator-based model below so the UI breakdown is exactly reproducible. Every score line item is stored and shown; the total is the capped sum.

   | Indicator | Points |
   |---|---:|
   | Scope mismatch (R-03) | 25 |
   | Beneficiary or profile change by employee | 20 |
   | Connected transfer within 60 minutes of the insider event | 20 |
   | Splitting pattern (R-05) | 25 |
   | Circular flow (R-06) | 20 |
   | Access burst or failed-auth pattern (R-01) | 15 |
   | After-hours privileged action (R-08), not suppressed | 5 |
   | Peer abnormality (R-07), scaled 0 to 15 by percentile above P95, only if peer group is at least 5 | 0 to 15 |
   | Evidence independence: `floor(10 * distinct_evidence_types / 4)` where types are access, change, transaction, login | 0 to 10 |
   | Repeat pattern for same subject in the last 30 days | 0 to 5 |

   Cap at 100.

2. **Confidence.** `confidence = min(0.95, 0.50 + 0.10 * distinct_evidence_types + (0.07 if peer baseline was computed and exceeded threshold else 0))`. Any finding with status `insufficient_evidence` is capped at 0.50. Scenario S1 must produce exactly 0.87.
3. **Severity is separate from score.** Severity comes from the rule definitions and aggregation logic in `Detection-Rules.md`. Score is for ranking within the queue.
4. **No LLM anywhere.** `PRD` says "use LLM only for wording"; this build skips it entirely. Explanation text comes from templates over `explanation_facts`.
5. **Data replay screen.** It is in the nav spec but on the "cut first" side for effort. Build a minimal version: list of ingestion batches with counts, quarantined records, and freshness. No streaming.
6. **Sensitive identifiers.** Account numbers masked by default (show last 4), device and IP shown as short hashes, click-to-copy reveals nothing extra in this prototype.

---

## 4. Seed data specification

Write seed files as CSV/JSON under `data/seed/`, generated by a deterministic script (`scripts/generate_seed.py`, seed 42), then load them through the ingestion pipeline (CP2). Do not insert directly into tables.

**Volume:** one synthetic bank (name it "Deccan Cooperative Bank (synthetic)") with 4 branches, about 60 employees, 400 customers, 600 accounts, roughly 6,000 background transactions and 12,000 background access events, all benign and plausible: business-hours skew, weekday skew, realistic amounts, role-appropriate actions.

**Roles:** teller, relationship_manager, customer_service, ops_batch_operator, security_admin, branch_manager, each with a permission set that includes branch scope and record-type scope.

**Every record carries:** `event_time`, `ingested_at`, `source_id`, and a `scenario_label` (null for background).

**Supporting tables required by the rules:** `case_assignments` (employee, customer, valid window), `batch_jobs` (job id, approved flag, window, operator), `oncall_approvals` (ticket id, employee, window), recurring-payment tags on transactions, `config` (thresholds).

**Scenarios** (IDs below are fixed so tests can assert on them):

| ID | Scenario | Key data | Expected |
|---|---|---|---|
| S1 | Insider beneficiary manipulation | Teller E-0417 (Pune branch) accesses customer C-2210 (Mumbai branch, no case assignment), event A-19 at 14:02; beneficiary change P-07 at 14:09; transfer T-88 at 14:20 to a new destination. E-0417's daily access volume sits at about P99 of teller peers | R-03 triggered, R-04 high, single aggregated alert, score 87, confidence 0.87, 3 evidence events |
| S2 | Transaction splitting | Four transfers (7.4L, 8.1L, 9.2L, 9.6L) from ACC-5031 and same-owner ACC-5032 to ACC-9907 within 20 hours; aggregate over threshold | R-05 triggered, medium |
| S2b | Decoy for S2 | Monthly salary disbursement to 40 accounts, each near threshold-adjacent amounts, tagged recurring and matching prior months | R-05 not triggered |
| S3 | Circular flow | ACC-6101 to ACC-6102 to ACC-6103 to ACC-6101 within 48 hours (12.0L, 11.6L, 11.2L); ACC-6103 shares a beneficiary with ACC-6101 | R-06 triggered, medium |
| S4 | Legitimate month-end batch | ops_batch_operator E-0880 retrieves 84 distinct customer records in 9 minutes under approved job JOB-ME-0930; six peers show similar volume | R-02 informational (would breach the absolute threshold, suppressed by approved job and baseline), no alert, "Monitored — no alert" record with reasons |
| S5 | Borderline | customer_service E-0512 accesses an out-of-branch customer with no assignment (R-03), and a transfer from that account occurs 3 hours later (outside the 60-minute R-04 window) | R-03 triggered medium, R-04 `insufficient_evidence`, alert recommends manual review, never high |
| S6 | Failed logins | E-0233: 7 failed logins across 2 devices in 11 minutes, then success from a new device | R-01 triggered |
| S7 | Small peer group and on-call | Three security_admin employees only. One performs after-hours privileged action with approved ticket TKT-4471 | R-07 `insufficient_evidence` (peer group under 5), R-08 suppressed |
| S8 | Assigned access | customer_service employee accesses out-of-branch customer under a valid case assignment | R-03 not triggered |

Also create `data/seed/bad/` with invalid records (missing ID, invalid timestamp, negative amount, unknown entity, duplicate event ID, ambiguous account match) to prove quarantine handling at CP2.

Write `backend/tests/expected_alerts.json` as the golden file from this table. Tests compare engine output to it.

---

## 5. Checkpoints

Each checkpoint lists deliverables and a gate. Implement `verify.py --cp N` so the gate is executable, not a manual check.

### CP0. Bootstrap and lock

- Initialize git, `.gitignore`, `.gitattributes`, folder layout.
- Read all five docs. Write `DECISIONS.md` with the section 3 conflicts and any others you find.
- `scripts/setup.py`, stub `scripts/verify.py`, backend health endpoint, frontend that renders and loads fonts from the bundle.

**Gate:** `setup.py` succeeds on a clean checkout; backend `/health` returns 200; frontend builds; `verify.py --cp 0` passes.

### CP1. Schema and deterministic seed

- SQLite schema for every table in `Architecture.md` section 4, plus the supporting tables in section 4 above. Every event-like table has `event_time`, `ingested_at`, `source_id`; findings have `rule_version`.
- `generate_seed.py` producing the files described above.

**Gate:** running the generator twice produces identical file hashes; all eight scenarios present; row counts within stated ranges; a test asserts specific IDs (A-19, P-07, T-88, E-0417, C-2210, ACC-9907, JOB-ME-0930, TKT-4471) exist with the stated timestamps.

### CP2. Ingestion and normalization

- Loader for CSV and JSON. Required-field validation, timestamp normalization to UTC, entity-reference validation, duplicate detection, ambiguous-entity detection (`UNRESOLVED_ENTITY` warning).
- Invalid records go to a quarantine table with a reason; the pipeline never crashes on bad input.
- Raw event provenance retained.

**Gate:** loading `data/seed/` yields zero quarantined records; loading `data/seed/bad/` quarantines exactly the expected records with correct reasons and does not abort; `reset_demo.py` rebuilds from scratch in under 10 seconds.

### CP3. Graph and feature layer

- Build a NetworkX temporal multigraph with the node and edge types from `Architecture.md` section 5; every edge carries timestamp and source event ID.
- Traversal: employee to access to customer/account to transaction/beneficiary.
- Feature builder: access volume by employee/role/branch/window, peer median and percentile (minimum peer group 5), out-of-scope count, near-threshold counts, destination concentration, access-to-transaction lag, cycle detection.
- Timeline query and shortest-evidence-path query.

**Gate:** for S1, the shortest path from E-0417 to T-88 returns the ordered chain A-19, P-07, T-88; peer percentile for E-0417 is at least 99; S4 operator sits inside peer baseline; a small peer group returns an "unavailable" flag, not a number.

### CP4. Rule engine, ledger, scoring

- Implement R-01 to R-08 exactly per `Detection-Rules.md`: structured findings with rule ID and version, status (`triggered`, `not_triggered`, `insufficient_evidence`), severity, confidence, evidence IDs, derived facts, thresholds, template explanation, recommended next action.
- Rules never mutate raw events and are independently testable.
- Suppressions and controls as written (approved jobs, case assignments, on-call tickets, recurring payments).
- Aggregation by employee, account, customer, destination and 24 to 72 hour window; a finding ledger so no event is counted twice.
- Scoring per section 3.
- Each explanation must answer the six questions in section 8 of `Detection-Rules.md`.

**Gate:** pytest reproduces the entire "Rule testing matrix" from `Detection-Rules.md` plus S1 to S8 from the golden file. S1 score is exactly 87 and confidence 0.87. S4 produces no alert above informational. S5 is medium with a manual-review recommendation. No evidence event appears in a finding ledger twice. Rerunning the engine is idempotent.

### CP5. API, cases, audit, export

- All endpoints from `Architecture.md` section 8, plus `/me`, `/rules`, `/monitored` (legitimate-activity records).
- Case create, assign, status change, notes. Dismiss requires a reason from the allowed set (legitimate batch, approved access, duplicate, insufficient evidence). Escalate returns an export preview.
- Audit log for every action with actor, timestamp, before/after status, rule version. Audit rows are append-only.
- Export as JSON and Markdown: events, timestamps, rule results, score breakdown, analyst notes, and a header stating the data is synthetic.
- Role checks on the API (analyst, supervisor, admin).

**Gate:** API test suite covers each endpoint, permission failures, invalid transitions and the S1 flow end to end (alert, evidence, case, assignment, note, export) without touching the database directly. Export for S1 contains exactly 3 evidence events, none duplicated. Alerts list responds in under 300 ms locally.

### CP6. Frontend foundation and alert queue

- Design system per section 6. Build tokens, layout shell (left nav, top bar with tenant, replay indicator, freshness, user switcher, reset control), persistent synthetic-data banner.
- Alert queue per `Product-Design-Specification.md` screen B, with all columns and filters, filter state preserved on return from detail.
- Keyboard navigation in the table.

**Gate:** Playwright loads the queue with zero console errors, shows the S1 alert at the top, filters work, load time under 5 seconds with a cold cache. Take screenshots at 1440x900 and 1280x720 and review them yourself against section 6 before passing.

### CP7. Alert detail and investigation graph

- Alert detail per screen C: header, explanation card (what happened, why it matters, evidence, what is missing, next step), score breakdown with each line item, evidence timeline, evidence table, notes, audit history.
- Investigation graph per screen D with the specified node shapes and edge styles, hover metadata, click-to-pin evidence, time slider, and a "shortest evidence path" button.
- Every graph selection has an evidence-list equivalent reachable by keyboard.
- "Why not an alert?" panel per screen E for S4, rendered in the same evidence style as suspicious alerts.
- Uncertainty states from section 7 of the design spec: no evidence, small peer group, stale data, ambiguous identity.

**Gate:** Playwright walks S1: queue to alert to evidence chain to graph path highlight, in at most three clicks from queue to a visible evidence chain. S4 shows "Monitored — no high-severity alert" with its four reasons. S7 shows the small-peer-group message. Zero console errors. Screenshots reviewed.

### CP8. Cases, overview, rule performance, data replay

- Case workspace per screen F: evidence checklist, notes, related alerts, next action, export, activity log.
- Overview per screen A. No vanity metrics. Show open high/medium alerts, alerts by rule, median evidence count, false-positive test status (from the seeded test set, visible), last ingestion time.
- Rule performance screen: per rule, seeded scenarios detected, benign scenarios correctly quiet, from real test results.
- Minimal data replay screen (section 3, item 5).

**Gate:** Playwright completes the full demo sequence from `Delivery-Phases.md` Phase 8 in one script: queue, S1 alert, evidence and graph, score breakdown, assign case and add note, S2 splitting, S4 legitimate, export bundle. Reset returns the app to a clean state and the script passes a second time.

### CP9. Hardening, audit and handoff

- Edge cases: missing timestamps excluded from temporal rules and flagged; conflicting timestamps; small peer groups; stale data indicator; ambiguous entities excluded from high-confidence paths.
- Confirm masking everywhere including the export and screenshots.
- Accessibility pass: keyboard reachability, focus visibility, severity shown as text plus shape, contrast at least 4.5:1 for body text (compute it, do not eyeball).
- Run the anti-AI audit in section 7 against the running app and the code.
- Write `README.md` (short, plain, how to run, how to reset, what is synthetic, known limits) and `docs/BUILD_REPORT.md` (gate results, deviations, decisions, remaining limitations).
- Capture backup screenshots into `docs/screenshots/`.

**Gate:** `python scripts/verify.py --cp 9` runs everything from a clean database and passes. Run it twice to confirm determinism. Clone the repo into a temp folder, run setup and dev from scratch, and confirm the app starts.

---

## 6. Design direction (this must not look AI-generated)

The spec calls for a calm investigation console. Build something that looks like internal tooling a bank's risk team actually uses: dense, quiet, literal.

**Do:**

- Dark charcoal-navy workspace. Suggested tokens: background `#0E1319`, surface `#151B23`, raised surface `#1B232D`, border `#263140`, text `#E8E4DC`, muted text `#8B98A9`, critical `#C25450`, high `#D9822B`, medium `#4C8DD6`, informational `#4E9F7D`, derived/explanatory text accent `#9B8AD6`. Adjust after contrast checks.
- Left-aligned everything. Dense tables with 32 px rows, sticky headers, tabular numerals, thin 1 px borders, 3 px maximum corner radius.
- IBM Plex Mono for IDs, timestamps, rule IDs, amounts. IBM Plex Sans for the rest. Sentence case throughout.
- Severity as a text label plus a small custom shape (square, triangle, circle, diamond) in inline SVG. Not color alone.
- Use the exact copy from the design spec for headers, empty states and warnings. Terse labels: `High · R-04`, `Evidence 3`, `Manual review`.
- Real-looking data. Names, branches and IDs follow a consistent internal scheme. Nothing placeholder.
- Simple bars in the overview drawn with plain SVG or CSS. No chart library unless it is clearly needed.

**Do not (each of these is a defect if found):**

- Gradients of any kind, gradient text, glow, glassmorphism, backdrop blur, neon accents.
- Purple-to-blue palettes, or violet used as a risk color. Violet appears only for derived text as the spec states.
- Rows of big-number stat cards with icon circles. Three-column feature grids. Hero sections. Centered marketing layouts.
- Heavy rounded corners (no `rounded-2xl` look), drop-shadow stacks, floating cards on cards.
- Emoji anywhere: UI, logs, commit messages, README, comments, seed data.
- Icon-library sprinkling (lucide, heroicons on every label). Hand-write the few SVG shapes needed; navigation is text.
- Pulsing dots, shimmer skeletons, bouncing or staggered entrance animations. Only 120 ms hover and drawer transitions.
- Default Inter or system-ui look. Generic names like "Acme", "Company X", "John Doe".
- Filler copy: "Welcome back", "Seamlessly", "Powered by AI", "Unlock insights", "Supercharge", exclamation marks, AI or sparkle badges.
- A chatbot panel.

**Code should not read as generated either:**

- No banner comments, no `// Step 1:` narration, no docstring on every function. Comment only the non-obvious why.
- Domain-specific names. Avoid `utils.py`, `helpers.ts`, `*Manager`, `*Handler`, `*Service` piles. Small modules named for what they do (`scope_check.py`, `threshold_window.py`).
- No dead code, no unused abstraction layers, no placeholder TODOs left in.
- README is short and plain. No badges, no emoji, no feature-list marketing.

---

## 7. Anti-AI audit (run at CP6, CP7, CP9)

Take Playwright screenshots of every screen at 1440x900 and 1280x720. Look at each one and answer honestly:

1. Would this pass as a screenshot from an internal risk tool? If it looks like a SaaS landing page or a template, redesign it.
2. Any gradient, glow, blur, emoji, decorative icon circle, or oversized rounded card? Remove it.
3. Is any text truncated, overflowing, overlapping, or misaligned? Fix it.
4. Is any number on screen not explainable from stored data? Fix it or remove it.
5. Does any string accuse a person? Replace it using the tone table in the design spec.
6. Grep the frontend for emoji code points, `gradient`, `backdrop-filter`, `box-shadow` (allow only on the evidence drawer overlay), `blur(`, and remote URLs. Remove hits.
7. Grep the codebase for banner comments and narration comments and clean them.

Record results in `docs/BUILD_REPORT.md`. Fix everything found before passing the gate.

---

## 8. Definition of done

- One command rebuilds the database; one command starts the app.
- S1 to S8 behave exactly as the golden file states; S1 shows score 87 and confidence 0.87.
- The legitimate batch scenario is visibly explained as monitored, not alerted.
- The borderline case recommends manual review and never reaches high severity.
- An analyst reaches evidence in three clicks or fewer, assigns a case, adds a note, exports a bundle, and the audit log shows every step.
- Every number on screen traces to stored events.
- All gates pass twice in a row from a clean database.
- `docs/BUILD_REPORT.md` and `README.md` exist and are accurate.

Begin with CP0 now. Do not ask me anything. Report only when CP9 has passed.
