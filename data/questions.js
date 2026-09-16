'use strict';

const SOURCE_CATALOG = {
  BHASHABENCH_LEGAL: {
    shortTitle: 'BhashaBench-Legal',
    title: 'BhashaBench-Legal via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original Indian-law MCQs, with current-law corrections where documented by the V8 validation audit.'
  },
  BHASHABENCH_FINANCE: {
    shortTitle: 'BhashaBench-Finance',
    title: 'BhashaBench-Finance via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original India-specific finance MCQs, with current-law corrections where documented by the V8 validation audit.'
  },
  NPTEL_ETHICAL_CORPORATION: {
    shortTitle: 'NPTEL — The Ethical Corporation',
    title: 'NPTEL / IIT Kharagpur — The Ethical Corporation (2019 assignments)',
    url: 'https://archive.nptel.ac.in/noc/courses/noc19/SEM2/noc19-mg56/',
    license: 'CC BY-NC-SA',
    licenseUrl: 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
    author: 'NPTEL / IIT Kharagpur course team',
    provenance: 'Pre-existing NPTEL assignment MCQs retained after IICA-domain relevance, currentness and duplicate screening. Stored separately because the licence is non-commercial/share-alike.'
  }
};

const OPEN_QUESTION_BANK = Array.isArray(window.OPEN_QUESTION_BANK) ? window.OPEN_QUESTION_BANK : [];
const NPTEL_QUESTION_BANK = Array.isArray(window.NPTEL_QUESTION_BANK) ? window.NPTEL_QUESTION_BANK : [];
const QUESTION_BANK = [...OPEN_QUESTION_BANK, ...NPTEL_QUESTION_BANK];
window.SOURCE_CATALOG = SOURCE_CATALOG;
window.QUESTION_BANK = QUESTION_BANK;
