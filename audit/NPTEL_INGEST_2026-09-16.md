# NPTEL ingest and deduplication — 16 September 2026

Scope: official NPTEL/IIT Kharagpur *The Ethical Corporation* Week 1 and Week 4 assignment material.

- 20 assignment questions were screened across the two official assignment papers.
- 7 single-answer questions were selected for direct IICA-domain relevance and durable governance/company-law value.
- Questions requiring multi-select support, carrying dated/obsolete legal formulations, falling outside the intended four domains, or substantially overlapping existing concepts were not imported.
- The curated 7 were then compared against every surviving Bhasha question using normalized exact matching plus a 0.90 SequenceMatcher near-duplicate threshold.
- Result: all 7 curated questions were unique enough to import; no curated question was rejected by the final stem-level duplicate gate.
- A stakeholder-theory assignment item was intentionally not curated because the surviving Bhasha bank already contains a direct stakeholder-theory question.
- No AI-authored questions were created or imported.

Licence handling: NPTEL question data is isolated in `data/nptel_questions.js` and marked CC BY-NC-SA; the application code remains separately MIT-licensed.
