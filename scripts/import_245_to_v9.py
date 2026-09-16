from __future__ import annotations
from pathlib import Path
from collections import Counter
import base64, gzip, json, re, shutil

ROOT=Path('.')
PAYLOAD=ROOT/'import_payload'
DATA=ROOT/'data'

chunks=sorted(PAYLOAD.glob('chunk_*.txt'))
if not chunks:
    raise SystemExit('No import payload chunks found')
encoded=''.join(p.read_text(encoding='utf-8').strip() for p in chunks)
raw=gzip.decompress(base64.b64decode(encoded))
source_file=DATA/'source_qa_questions.js'
source_file.write_bytes(raw)
text=raw.decode('utf-8')
m=re.search(r'window\.SOURCE_QA_QUESTION_BANK\s*=\s*(\[.*\]);\s*$', text, re.S)
if not m:
    raise SystemExit('Could not parse SOURCE_QA_QUESTION_BANK payload')
questions=json.loads(m.group(1))
assert len(questions)==245
assert len({q['id'] for q in questions})==245
assert len({re.sub(r'\W+',' ',q['question'].lower()).strip() for q in questions})==245
assert all(q['aiGenerated'] is False for q in questions)
assert all(q['originType']=='source_qa_converted_mcq' for q in questions)
assert all(q['choicesGenerated']=='assistant-generated-distractors' for q in questions)
assert all(len(q['options'])==4 and len(set(q['options']))==4 and q['options'][q['answer']] for q in questions)

cat=Counter(q['category'] for q in questions)
diff=Counter(q['difficulty'] for q in questions)
sources=Counter(q['sourceId'] for q in questions)
assert cat=={'Companies Law':108,'Corporate Governance':50,'Securities Law':49,'Basic Accountancy':38}
assert diff=={'S':181,'M':60,'H':4}
assert sources=={'INDIANLEGAL_QA':242,'RMANI_INDIAN_LEGAL':3}

manifest={
  'schemaVersion':6,
  'build':'V9-validated-source-qa-370',
  'generatedAt':'2026-09-16T12:30:00Z',
  'activeQuestionCount':370,
  'corpusCount':370,
  'sourceOriginalMcqCount':125,
  'sourceQaConvertedCount':245,
  'bhashaActiveCount':118,
  'nptelImportedCount':7,
  'indianLegalQaConvertedCount':242,
  'rmaniConvertedCount':3,
  'retiredAfterValidationCount':13,
  'validationRequiredCount':0,
  'sourceQualityPassCount':370,
  'aiQuestionCount':0,
  'assistantGeneratedDistractorQuestionCount':245,
  'categoryCounts':{'Basic Accountancy':47,'Companies Law':188,'Corporate Governance':61,'Securities Law':74},
  'difficultyCounts':{'H':7,'M':102,'S':261},
  'sourceCounts':{'BHASHABENCH_FINANCE':37,'BHASHABENCH_LEGAL':81,'NPTEL_ETHICAL_CORPORATION':7,'INDIANLEGAL_QA':242,'RMANI_INDIAN_LEGAL':3},
  'policy':'V9 contains 125 validated source-original/corrected MCQs plus 245 current-law-validated open-licensed source Q&A items converted to MCQ. No active question stem is AI-authored. The 245 converted items use assistant-generated distractors and are explicitly labelled as such.'
}
(DATA/'bank_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

questions_js="""'use strict';

const SOURCE_CATALOG = {
  BHASHABENCH_LEGAL: {
    shortTitle: 'BhashaBench-Legal', title: 'BhashaBench-Legal via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi', license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/', author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original Indian-law MCQs, with current-law corrections where documented by the V8 validation audit.'
  },
  BHASHABENCH_FINANCE: {
    shortTitle: 'BhashaBench-Finance', title: 'BhashaBench-Finance via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi', license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/', author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original India-specific finance MCQs, with current-law corrections where documented by the V8 validation audit.'
  },
  NPTEL_ETHICAL_CORPORATION: {
    shortTitle: 'NPTEL — The Ethical Corporation', title: 'NPTEL / IIT Kharagpur — The Ethical Corporation (2019 assignments)',
    url: 'https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/', license: 'CC BY-NC-SA',
    licenseUrl: 'https://creativecommons.org/licenses/by-nc-sa/4.0/', author: 'NPTEL / IIT Kharagpur course team',
    provenance: 'Pre-existing NPTEL assignment MCQs retained after IICA-domain relevance, currentness and duplicate screening.'
  },
  INDIANLEGAL_QA: {
    shortTitle: 'IndianLegal-QA', title: 'IndianLegal-QA',
    url: 'https://huggingface.co/datasets/Sakib-Dalal/IndianLegal-QA', license: 'Apache-2.0',
    licenseUrl: 'https://www.apache.org/licenses/LICENSE-2.0', author: 'Sakib Dalal / dataset contributors',
    provenance: 'Open-licensed Indian legal Q&A filtered to IICA scope and validated against current law. Source propositions were converted to MCQs; distractors were created for this tool.'
  },
  RMANI_INDIAN_LEGAL: {
    shortTitle: 'Indian Legal Dataset', title: 'RMani1 Indian Legal Dataset — Indian Law',
    url: 'https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law', license: 'MIT',
    licenseUrl: 'https://opensource.org/license/mit', author: 'RMani1 / dataset contributors',
    provenance: 'Open-licensed Indian-law Q&A filtered to IICA scope and validated against current law. Source propositions were converted to MCQs; distractors were created for this tool.'
  }
};

const OPEN_QUESTION_BANK = Array.isArray(window.OPEN_QUESTION_BANK) ? window.OPEN_QUESTION_BANK : [];
const NPTEL_QUESTION_BANK = Array.isArray(window.NPTEL_QUESTION_BANK) ? window.NPTEL_QUESTION_BANK : [];
const SOURCE_QA_QUESTION_BANK = Array.isArray(window.SOURCE_QA_QUESTION_BANK) ? window.SOURCE_QA_QUESTION_BANK : [];
const QUESTION_BANK = [...OPEN_QUESTION_BANK, ...NPTEL_QUESTION_BANK, ...SOURCE_QA_QUESTION_BANK];
window.SOURCE_CATALOG = SOURCE_CATALOG;
window.QUESTION_BANK = QUESTION_BANK;
window.OPEN_BANK_MANIFEST = __MANIFEST__;
""".replace('__MANIFEST__',json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
(DATA/'questions.js').write_text(questions_js,encoding='utf-8')

index=Path('index.html').read_text(encoding='utf-8')
needle='  <script src="data/nptel_questions.js"></script>\n'
insert=needle+'  <script src="data/source_qa_questions.js"></script>\n'
if 'data/source_qa_questions.js' not in index:
    if needle not in index: raise SystemExit('index insertion point missing')
    index=index.replace(needle,insert)
Path('index.html').write_text(index,encoding='utf-8')

sw=Path('sw.js').read_text(encoding='utf-8')
sw=re.sub(r"const CACHE='[^']+';", "const CACHE='director-mock-v9-source-qa-370';", sw, count=1)
if "'data/source_qa_questions.js'" not in sw:
    sw=sw.replace("'data/nptel_questions.js',", "'data/nptel_questions.js','data/source_qa_questions.js',")
Path('sw.js').write_text(sw,encoding='utf-8')

app=Path('app.js').read_text(encoding='utf-8')
old="type === 'preexisting_qa_converted' ? 'Pre-existing QA → MCQ'"
new="(type === 'preexisting_qa_converted' || type === 'source_qa_converted_mcq') ? 'Source QA → MCQ'"
if old not in app: raise SystemExit('app source type label patch point missing')
app=app.replace(old,new)
app=app.replace("converted: eligible.filter(q => q.originType === 'preexisting_qa_converted').length", "converted: eligible.filter(q => q.originType === 'preexisting_qa_converted' || q.originType === 'source_qa_converted_mcq').length")
old_footer='The active mock bank uses only pre-existing openly licensed questions; no AI-authored question stems are served. Pre-existing QA items converted to MCQ use deterministic, non-AI distractors. Every item displays provenance, licence and S/M/H difficulty. Some source-marked answers and current-law thresholds remain flagged for validation.'
new_footer='The active mock bank uses openly licensed sourced material; no AI-authored question stems are served. Source-QA items converted to MCQ use assistant-generated distractors and are labelled accordingly. Every item displays provenance, licence and S/M/H difficulty. Active items were reviewed for current-law suitability as of the build review date.'
if old_footer not in app: raise SystemExit('app footer patch point missing')
app=app.replace(old_footer,new_footer)
Path('app.js').write_text(app,encoding='utf-8')

readme="""# Director Mock India — V9 Validated Source Bank

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

The 245 added questions come from a 622-item screened source-Q&A pool. Each retained item was classified KEEP or REWRITE, checked for IICA relevance/current-law suitability, then converted into a four-option MCQ. 377 screened candidates were retired as off-scope, obsolete/wrong or low-value/duplicative and are not served by the app.

## Mock format

- 50 questions
- 75 minutes
- 50% app pass threshold
- Per mock: 30 Companies Law, 10 Securities Law, 6 Basic Accountancy, 4 Corporate Governance.
- Questions and answer choices are shuffled.
- Practice, history, answer review, PWA/offline support and responsive layouts are included.

## Important

This is an unofficial educational preparation tool and is not affiliated with IICA, MCA, SEBI or NPTEL. Regulations can change; the active bank was reviewed on 16 September 2026.
"""
Path('README.md').write_text(readme,encoding='utf-8')

sources_md="""# Sources

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
"""
Path('SOURCES.md').write_text(sources_md,encoding='utf-8')

lic=Path('QUESTION_BANK_LICENSE.md').read_text(encoding='utf-8')
extra="""

## IndianLegal-QA converted rows
`data/source_qa_questions.js` includes 242 source propositions from IndianLegal-QA under **Apache-2.0**, converted to MCQ form after validation. Distractors created for this tool are identified in each row.

## RMani1 converted rows
The same file includes 3 source propositions from the RMani1 Indian Legal Dataset under **MIT**, converted to MCQ form after validation.
"""
if '## IndianLegal-QA converted rows' not in lic:
    lic=lic.rstrip()+extra+'\n'
Path('QUESTION_BANK_LICENSE.md').write_text(lic,encoding='utf-8')

# Payload is temporary transport, not part of the finished repository.
shutil.rmtree(PAYLOAD)
print(json.dumps({'imported':len(questions),'categories':cat,'difficulty':diff,'sources':sources,'manifest':manifest},default=dict,indent=2))
