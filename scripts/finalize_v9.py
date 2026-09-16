from pathlib import Path
import json, re, shutil

# Truthful UI provenance wording.
app = Path('app.js')
text = app.read_text(encoding='utf-8')
old_footer = 'The active mock bank uses only pre-existing openly licensed questions; no AI-authored question stems are served. Pre-existing QA items converted to MCQ use deterministic, non-AI distractors. Every item displays provenance, licence and S/M/H difficulty. Some source-marked answers and current-law thresholds remain flagged for validation.'
new_footer = 'The active mock bank uses openly licensed sourced material; no AI-authored question stems are served. Source-QA items converted to MCQ use assistant-generated distractors and are labelled accordingly. Every item displays provenance, licence and S/M/H difficulty. Active items were reviewed for current-law suitability as of the build review date.'
if old_footer not in text:
    raise SystemExit('Expected V8 footer text not found')
text = text.replace(old_footer, new_footer)
app.write_text(text, encoding='utf-8')

# Offline cache: cache V9 source shards and loader.
sw = Path('sw.js')
s = sw.read_text(encoding='utf-8')
s = re.sub(r"const CACHE='[^']+';", "const CACHE='director-mock-v9-source-qa-370';", s, count=1)
for name in [*(f'data/source_qa_{i:02d}.js' for i in range(1, 23)), 'data/source_qa_compact_loader.js']:
    if name not in s:
        s = s.replace("'data/nptel_questions.js',", f"'data/nptel_questions.js','{name}',", 1)
sw.write_text(s, encoding='utf-8')

manifest = {
  'schemaVersion': 6,
  'build': 'V9-validated-source-qa-370',
  'generatedAt': '2026-09-16T12:30:00Z',
  'activeQuestionCount': 370,
  'preexistingCount': 370,
  'corpusCount': 370,
  'sourceOriginalMcqCount': 125,
  'sourceQaConvertedCount': 245,
  'bhashaActiveCount': 118,
  'nptelImportedCount': 7,
  'indianLegalQaConvertedCount': 242,
  'rmaniConvertedCount': 3,
  'retiredAfterValidationCount': 13,
  'validationRequiredCount': 0,
  'sourceQualityPassCount': 370,
  'aiQuestionCount': 0,
  'assistantGeneratedDistractorQuestionCount': 245,
  'categoryCounts': {'Basic Accountancy': 47, 'Companies Law': 188, 'Corporate Governance': 61, 'Securities Law': 74},
  'difficultyCounts': {'H': 7, 'M': 102, 'S': 261},
  'sourceCounts': {'BHASHABENCH_FINANCE': 37, 'BHASHABENCH_LEGAL': 81, 'NPTEL_ETHICAL_CORPORATION': 7, 'INDIANLEGAL_QA': 242, 'RMANI_INDIAN_LEGAL': 3},
  'policy': 'V9 contains 125 validated source-original/corrected MCQs plus 245 current-law-validated open-licensed source Q&A items converted to MCQ. No active question stem is AI-authored. The 245 converted items use assistant-generated distractors and are explicitly labelled as such.'
}
Path('data/bank_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

Path('README.md').write_text('''# Director Mock India — V9 Validated Source Bank

Static, mobile-first PWA for practising the Indian Independent Director proficiency-assessment format.

## Active question bank

- **370 validated sourced questions are active.**
- Source-original/corrected MCQs: **125** (118 BhashaBench + 7 NPTEL).
- Validated open-source Q&A converted to MCQ: **245** (242 IndianLegal-QA + 3 RMani1).
- The converted questions preserve the validated source proposition; their distractors were created for this tool and are labelled `assistant-generated-distractors`.
- Categories: Basic Accountancy: 47, Companies Law: 188, Corporate Governance: 61, Securities Law: 74.
- Difficulty: H: 7, M: 102, S: 261.
- Validation-required active questions: **0**.
- AI-authored question stems: **0**.

## Validation status

The 245 added questions come from a 622-item screened source-Q&A pool. Each retained item was classified KEEP or REWRITE, checked for IICA relevance/current-law suitability, then converted into a four-option MCQ. The 377 rejected candidates remain outside the active bank.

## Mock format

- 50 questions
- 75 minutes
- 50% app pass threshold
- Per mock: 30 Companies Law, 10 Securities Law, 6 Basic Accountancy, 4 Corporate Governance.
- Questions and answer choices are shuffled.
- Practice, history, answer review, PWA/offline support and responsive layouts are included.

## Important

This is an unofficial educational preparation tool and is not affiliated with IICA, MCA, SEBI or NPTEL. Regulations can change; the active bank was reviewed on 16 September 2026.
''', encoding='utf-8')

Path('SOURCES.md').write_text('''# Sources

## BhashaBench — 118 active MCQs
- https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi
- Licence: CC BY 4.0

## NPTEL / IIT Kharagpur — 7 active MCQs
- https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/
- Licence: CC BY-NC-SA

## IndianLegal-QA — 242 active source-Q&A conversions
- https://huggingface.co/datasets/Sakib-Dalal/IndianLegal-QA
- Licence: Apache-2.0
- Q&A propositions were filtered to the IICA scope, current-law validated, then converted to four-option MCQs. The distractors were created for this tool; these are not represented as source-original MCQs.

## RMani1 Indian Legal Dataset — 3 active source-Q&A conversions
- https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law
- Licence: MIT
- Same source-Q&A conversion treatment as above.

## Excluded sources
Public coaching/test-prep pages and datasets without a clear reusable licence are not copied into the active bank. No AI/synthetic question stems are included in V9.
''', encoding='utf-8')

lic = Path('QUESTION_BANK_LICENSE.md')
l = lic.read_text(encoding='utf-8').rstrip()
if '## IndianLegal-QA converted rows' not in l:
    l += '''\n\n## IndianLegal-QA converted rows\n`data/source_qa_*.js` includes 242 source propositions from IndianLegal-QA under **Apache-2.0**, converted to MCQ form after validation. Distractors created for this tool are identified in the runtime provenance.\n\n## RMani1 converted rows\nThe source-QA shards include 3 source propositions from the RMani1 Indian Legal Dataset under **MIT**, converted to MCQ form after validation.\n'''
lic.write_text(l + '\n', encoding='utf-8')

# Remove abandoned opaque transport and its unused importer.
shutil.rmtree('import_payload', ignore_errors=True)
Path('scripts/import_245_to_v9.py').unlink(missing_ok=True)
