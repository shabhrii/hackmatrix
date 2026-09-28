# Decisions log

| Date | Question | Choice | Reason |
|---|---|---|---|
| 2026-09-28 | Score formula: Architecture.md gives weighted rule-count formula; Product Design Spec shows 25+20+20+15+7=87 breakdown | Indicator-based model from Build Script section 3 with 10 specific line items, capped at 100 | Build script resolves spec conflicts; indicator model makes UI breakdown reproducible |
| 2026-09-28 | Confidence calculation not specified consistently | `min(0.95, 0.50 + 0.10 * distinct_evidence_types + 0.07 if peer baseline computed and exceeded)`. `insufficient_evidence` capped at 0.50. S1 must produce 0.87 | Build script section 3 item 2 |
| 2026-09-28 | Severity vs score relationship unclear | Severity comes from rule definitions and aggregation in Detection-Rules.md. Score is for ranking within the queue only | Build script section 3 item 3 |
| 2026-09-28 | PRD says "use LLM only for wording" | No LLM anywhere. Explanation text from templates filled with derived facts | Build script section 3 item 4 — offline requirement |
| 2026-09-28 | Data replay screen in nav spec but effort unclear | Minimal version: list of ingestion batches with counts, quarantined records, freshness. No streaming | Build script section 3 item 5 — on "cut first" side |
| 2026-09-28 | Sensitive identifier display rules | Account numbers masked (show last 4), device and IP as short hashes, click-to-copy reveals nothing extra in prototype | Build script section 3 item 6 |
| 2026-09-28 | Architecture.md suggests Tailwind or component library | Plain CSS with design tokens, no Tailwind, no component library | Build script section 1 locked decision |
| 2026-09-28 | Architecture.md suggests React Flow or D3 as alternatives | Cytoscape.js for the graph | Build script section 1 locked decision |
