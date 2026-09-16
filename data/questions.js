'use strict';

const SOURCE_CATALOG = {
  BHASHABENCH_LEGAL: {
    shortTitle: 'BhashaBench-Legal',
    title: 'BhashaBench-Legal via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original Indian-law MCQs. Only rows mapped directly to IICA Companies Law, Securities Law or Corporate Governance are retained.'
  },
  BHASHABENCH_FINANCE: {
    shortTitle: 'BhashaBench-Finance',
    title: 'BhashaBench-Finance via BhashaBench-Multi',
    url: 'https://huggingface.co/datasets/bharatgenai/BhashaBench-Multi',
    license: 'CC BY 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by/4.0/',
    author: 'BharatGen AI / BhashaBench authors',
    provenance: 'Source-original India-specific finance MCQs. Only rows mapped directly to the IICA four-domain syllabus are retained.'
  }
};

const OPEN_QUESTION_BANK = Array.isArray(window.OPEN_QUESTION_BANK) ? window.OPEN_QUESTION_BANK : [];
const QUESTION_BANK = [...OPEN_QUESTION_BANK];
window.SOURCE_CATALOG = SOURCE_CATALOG;
window.QUESTION_BANK = QUESTION_BANK;
