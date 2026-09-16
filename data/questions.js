'use strict';

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
    provenance: 'Open-licensed Indian legal Q&A filtered to IICA scope and validated against current law; source propositions were converted to MCQs and distractors were created for this tool.'
  },
  INDIAFINBENCH: {
    shortTitle: 'IndiaFinBench', title: 'IndiaFinBench',
    url: 'https://github.com/Rajveer-code/IndiaFinBench', license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/', author: 'Rajveer Singh Pall / IndiaFinBench contributors',
    provenance: 'Expert-annotated India financial-regulation Q&A; promoted items were revalidated against current SEBI consolidated primary sources before MCQ conversion.'
  },
  INDIAN_REGULATORY_BFSI: {
    shortTitle: 'Indian Regulatory BFSI Benchmark', title: 'Indian Regulatory BFSI Benchmark v1',
    url: 'https://github.com/uditjainstjis/indian-regulatory-bfsi-benchmark', license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/', author: 'Udit Jain / benchmark contributors',
    provenance: 'Hand-curated RBI/SEBI benchmark Q&A; promoted SEBI items were revalidated against current SEBI primary sources before MCQ conversion.'
  },
  RMANI_INDIAN_LEGAL: {
    shortTitle: 'Indian Legal Dataset', title: 'RMani1 Indian Legal Dataset — Indian Law',
    url: 'https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law', license: 'MIT',
    licenseUrl: 'https://opensource.org/license/mit', author: 'RMani1 / dataset contributors',
    provenance: 'Open-licensed Indian-law Q&A filtered to IICA scope and validated against current law; source propositions were converted to MCQs and distractors were created for this tool.'
  }
};

const OPEN_QUESTION_BANK = Array.isArray(window.OPEN_QUESTION_BANK) ? window.OPEN_QUESTION_BANK : [];
const NPTEL_QUESTION_BANK = Array.isArray(window.NPTEL_QUESTION_BANK) ? window.NPTEL_QUESTION_BANK : [];
const SOURCE_QA_QUESTION_BANK = Array.isArray(window.SOURCE_QA_QUESTION_BANK) ? window.SOURCE_QA_QUESTION_BANK : [];
const ADDITIONAL_VALIDATED_QUESTION_BANK = Array.isArray(window.ADDITIONAL_VALIDATED_QUESTION_BANK) ? window.ADDITIONAL_VALIDATED_QUESTION_BANK : [];
const QUESTION_BANK = [...OPEN_QUESTION_BANK, ...NPTEL_QUESTION_BANK, ...SOURCE_QA_QUESTION_BANK, ...ADDITIONAL_VALIDATED_QUESTION_BANK];
window.SOURCE_CATALOG = SOURCE_CATALOG;
window.QUESTION_BANK = QUESTION_BANK;
window.OPEN_BANK_MANIFEST = {
  "schemaVersion": 7,
  "build": "V12-current-sebi-validated-397",
  "generatedAt": "2026-09-16T00:00:00Z",
  "activeQuestionCount": 397,
  "preexistingCount": 397,
  "corpusCount": 397,
  "sourceOriginalMcqCount": 125,
  "sourceQaConvertedCount": 272,
  "additionalPrimaryValidatedCount": 27,
  "bhashaActiveCount": 118,
  "nptelImportedCount": 7,
  "indianLegalQaConvertedCount": 242,
  "rmaniConvertedCount": 3,
  "retiredAfterValidationCount": 13,
  "validationRequiredCount": 0,
  "sourceQualityPassCount": 397,
  "aiQuestionCount": 0,
  "assistantGeneratedDistractorQuestionCount": 272,
  "categoryCounts": {
    "Basic Accountancy": 47,
    "Companies Law": 188,
    "Corporate Governance": 67,
    "Securities Law": 95
  },
  "difficultyCounts": {
    "H": 10,
    "M": 109,
    "S": 278
  },
  "sourceCounts": {
    "BHASHABENCH_FINANCE": 37,
    "BHASHABENCH_LEGAL": 81,
    "NPTEL_ETHICAL_CORPORATION": 7,
    "INDIANLEGAL_QA": 242,
    "RMANI_INDIAN_LEGAL": 3,
    "INDIAFINBENCH": 27
  },
  "policy": "V12 contains the prior 370 validated sourced questions plus 27 additional open-licensed source Q&A items revalidated against current SEBI consolidated primary sources on 16 September 2026 and converted to MCQ. No active question stem is AI-authored; converted items use assistant-generated distractors and are explicitly labelled as such."
};
