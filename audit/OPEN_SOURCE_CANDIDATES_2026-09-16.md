# Director Mock India — additional open-source question research

Research date: 2026-09-16

Purpose: identify legitimate pre-existing/open material beyond BhashaBench that can expand the Indian Independent Director exam-preparation bank without misrepresenting provenance or licensing.

## Executive result

The strongest additional source found is **NPTEL**, especially IIT Kharagpur's **Business Law for Managers** and **The Ethical Corporation**. These courses contain assignment MCQs directly relevant to Companies Act, corporate governance, directors, CSR and securities regulation. NPTEL's current/archive site labels distributed material under Creative Commons **CC BY-NC-SA** terms.

A second strong source is **Sakib-Dalal/IndianLegal-QA** on Hugging Face, licensed **Apache-2.0**. It is large and legally broad, but it is Q&A rather than an original MCQ bank; any multiple-choice questions derived from it must be marked as converted/derived questions rather than pre-existing MCQs.

Publicly visible coaching pages, no-license datasets and synthetic/AI datasets should **not** be counted as open pre-existing questions.

## Candidate register

| Priority | Source | Format | Licence / reuse status | IICA relevance | Recommended use |
|---|---|---|---|---|---|
| A | NPTEL — Business Law for Managers, IIT Kharagpur | Course assignment MCQs | NPTEL site/archive: CC BY-NC-SA | High: Companies Act, CSR, directors, governance, securities/PIT | Import only after question-by-question current-law validation and with separate CC BY-NC-SA attribution/licensing treatment |
| A | NPTEL — The Ethical Corporation | Course assignment MCQs | NPTEL site/archive: CC BY-NC-SA | High for governance, ethics, CSR, stakeholder duties | Same treatment as above |
| B | Sakib-Dalal/IndianLegal-QA | Q&A dataset; ~120k legal QA records | Apache-2.0 | Potentially high after filtering Companies Act / securities / governance | Filter relevant rows; retain source Q&A provenance; if converted to MCQ, label as derived/converted rather than verbatim MCQ |
| C | RMani1/indian-legal-dataset-indian-law | Q&A dataset; ~1.5k records | MIT | Broad Indian law; likely limited direct IICA coverage | Secondary source after filtering |
| Grounding only | vaquill/open-india-law | Indian primary/legal corpus | CC BY 4.0 | Very useful for statutory validation, not a question bank | Use to validate/ground questions; do not count source text as pre-existing MCQs |
| Exclude pending licence | ris322612 Indian corporate-law QA datasets | Q&A | No clear reusable licence found | Corporate-law relevant | Do not import unless an explicit licence or permission is established |
| Exclude | Public coaching/test-prep pages | Web MCQs | Usually copyrighted/no open licence | Often relevant | Can be used as discovery leads only; do not copy questions into the bank without permission |
| Exclude from “pre-existing sourced” count | Synthetic/AI Indian-law datasets | AI-generated QA | Licence varies | Varies | May inform later AI-question generation but must never be presented as human/source-original questions |

## NPTEL findings

### Business Law for Managers

Official course coverage includes company/corporate law and related regulatory material. Indexed archived assignments expose actual multiple-choice questions, including topics such as:

- separate legal personality and company forms;
- AGM notice periods;
- CSR applicability and qualifying/excluded activities;
- board composition and directors;
- corporate governance committees/conflicts;
- SEBI-related governance concepts.

At least **20 assignment MCQs** were recoverable from indexed Week 1 and Week 2 material during this research pass. Additional weeks should be enumerated directly from the NPTEL archive before ingestion.

Important: the age of individual NPTEL assignments means each legal answer still requires a current-law check. Some indexed questions clearly use historical provisions or wording. Open licensing does not make an obsolete answer suitable for the current mock bank.

### The Ethical Corporation

This NPTEL course contains governance/ethics assignments that are relevant to the IICA governance domain. It is useful particularly for:

- corporate governance principles;
- stakeholder/shareholder duties;
- ethical decision-making;
- CSR and board responsibility.

Again, ingest only questions that map directly to the intended syllabus and remain current.

### NPTEL licensing constraint

The current NPTEL/archive pages identify distributed material as Creative Commons **Attribution-NonCommercial-ShareAlike (CC BY-NC-SA)**. This is materially different from the repository's MIT-licensed application code and from BhashaBench CC BY 4.0 content.

Therefore:

1. Do not imply that copied NPTEL question text is MIT-licensed.
2. Keep NPTEL question data and attribution clearly separable from application code.
3. Preserve source/course/assignment URL, author/institution, licence and attribution for every imported question.
4. Because of the NonCommercial and ShareAlike terms, do not merge NPTEL text into a bank that is represented as unrestricted MIT/CC-BY data.
5. If the tool may later become commercial, obtain permission or avoid verbatim NPTEL question text.

## Apache/MIT Q&A candidates

### Sakib-Dalal/IndianLegal-QA

This is the most promising open non-NPTEL dataset found. It is licensed Apache-2.0 and contains a large multi-format Indian-law QA corpus.

Recommended pipeline:

1. Filter by statute/topic names such as Companies Act 2013, SEBI Act, Securities Contracts (Regulation) Act, Depositories Act and governance/accounting-adjacent material.
2. Remove rows that are obsolete, state-specific/non-IICA, duplicative or poorly grounded.
3. Validate retained source answers against current authoritative law.
4. Preserve the original Q&A as source material.
5. If converted to a 4-option question, record `originType: source_qa_converted_mcq`, preserve the source answer, and mark distractors as generated/curated. Do **not** call it a verbatim/pre-existing MCQ.

### RMani1/indian-legal-dataset-indian-law

This MIT dataset is much smaller and broad rather than corporate-law focused. It is worth a targeted filter after the larger Apache-licensed source, but is unlikely to add hundreds of directly usable IICA questions by itself.

## Sources deliberately not imported

### No-license corporate-law QA datasets

Some Hugging Face corporate-law QA datasets look topically attractive but expose no licence that clearly authorizes redistribution. They should remain discovery-only until the publisher adds a licence or gives permission.

### Coaching websites / exam-prep pages

A publicly accessible MCQ page is not automatically open content. Unless the site states a licence permitting reuse, the questions should not be copied into the GitHub bank. Links may be retained for manual review/discovery.

### AI-generated datasets

AI/synthetic law QA can be useful later when producing the requested 100–200 AI-authored questions, but those records must stay in the AI-generated provenance class and must not inflate the “pre-existing sourced questions” total.

## Recommended next extraction order

1. **NPTEL Business Law for Managers** — enumerate all assignment weeks; extract only direct-IICA MCQs; validate current law; deduplicate against BhashaBench.
2. **NPTEL The Ethical Corporation** — extract direct governance/CSR/director questions and validate.
3. **Sakib-Dalal/IndianLegal-QA** — programmatically filter Companies Act/SEBI/securities/governance source Q&A, then score for direct syllabus fit.
4. **RMani1 dataset** — run same filter as a lower-volume supplemental source.
5. Keep all no-license pages in a separate `discovery_only` register rather than importing question text.

## Provenance fields to require for every future sourced item

- `sourceId`
- `sourceTitle`
- `sourceUrl`
- `sourceLicense`
- `sourceAuthorOrInstitution`
- `originType` (`preexisting_verbatim_mcq`, `source_qa_converted_mcq`, etc.)
- `choicesGenerated` (`source-original`, `curated`, `ai-generated`)
- `retrievedAt`
- `lawValidatedAt`
- `lawValidationSources`
- `validationStatus`

This prevents a converted open Q&A item or an AI-written distractor set from being confused with a verbatim source-original MCQ.

## Reference links

- NPTEL main/archive: https://nptel.ac.in/ and https://archive.nptel.ac.in/
- Business Law for Managers: https://onlinecourses.nptel.ac.in/noc21_mg100/preview
- The Ethical Corporation: https://onlinecourses.nptel.ac.in/noc23_mg63/preview
- IndianLegal-QA: https://huggingface.co/datasets/Sakib-Dalal/IndianLegal-QA
- RMani1 Indian legal dataset: https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law
- Open India Law: https://huggingface.co/datasets/vaquill/open-india-law

## Current recommendation

Do **not** bulk-import anything solely because it is public or downloadable. The target bank should distinguish:

- **source-original MCQ**;
- **source Q&A converted to MCQ**;
- **AI-authored question**;
- **discovery-only/no-reuse-permission material**.

That gives the final 500+ bank defensible provenance and avoids mixing copied, transformed and AI-authored questions under one label.
