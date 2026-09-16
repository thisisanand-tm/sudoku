# Director Mock India — V8 Validated Source Bank

Static, mobile-first PWA for practising the Indian Independent Director proficiency-assessment format.

## Active question bank

- **125 pre-existing sourced questions are active.**
- BhashaBench active after validation/retirement: **118**.
- NPTEL pre-existing assignment questions imported after screening/deduplication: **7**.
- Retired after current-law/quality validation: **13**.
- Categories: Basic Accountancy: 9, Companies Law: 80, Corporate Governance: 11, Securities Law: 25.
- Difficulty: H: 3, M: 42, S: 80.
- Validation-required active questions: **0**.
- AI-authored question count: **0**.

## Validation status

The 88 questions previously flagged for validation were individually reviewed. The 37 valid-as-is items were cleared, 15 factual/reference defects were corrected, 23 useful items were rewritten for current law/clarity, and 13 obsolete/ambiguous items were retired from active sampling. Retired source rows are preserved in `data/retired_questions.json`.

## NPTEL source addition

Seven pre-existing questions from NPTEL/IIT Kharagpur's *The Ethical Corporation* assignments were added after direct IICA-domain relevance, currentness and duplicate screening. NPTEL question text is kept in `data/nptel_questions.js` because it carries **CC BY-NC-SA** terms and must remain licence-distinct from the MIT application code and the CC BY 4.0 BhashaBench data.

## Mock format

- 50 questions
- 75 minutes
- 50% app pass threshold
- Per mock: 30 Companies Law, 10 Securities Law, 6 Basic Accountancy, 4 Corporate Governance.
- Questions and answer choices are shuffled.
- Practice, history, answer review, PWA/offline support and responsive layouts are included.

## Important

This is an unofficial educational preparation tool and is not affiliated with IICA, MCA, SEBI or NPTEL. Legal/regulatory questions should still be rechecked when laws or regulations change.
