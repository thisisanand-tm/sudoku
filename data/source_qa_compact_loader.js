'use strict';

const rawSourceQa = [];
for (let i = 1; i <= 22; i += 1) {
  const key = `SOURCE_QA_COMPACT_${String(i).padStart(2, '0')}`;
  const part = window[key];
  if (Array.isArray(part)) rawSourceQa.push(...part);
}

if (rawSourceQa.length !== 245) {
  throw new Error(`V9 source-QA bank expected 245 rows, found ${rawSourceQa.length}`);
}

const sourceMeta = {
  I: { sourceId: 'INDIANLEGAL_QA', sourceLicense: 'Apache-2.0', sourceUrl: 'https://huggingface.co/datasets/Sakib-Dalal/IndianLegal-QA' },
  R: { sourceId: 'RMANI_INDIAN_LEGAL', sourceLicense: 'MIT', sourceUrl: 'https://huggingface.co/datasets/RMani1/indian-legal-dataset-indian-law' }
};

window.SOURCE_QA_QUESTION_BANK = rawSourceQa.map((x) => {
  const meta = sourceMeta[x.s];
  if (!meta) throw new Error(`Unknown source code for ${x.id}`);
  if (!Array.isArray(x.o) || x.o.length !== 4 || new Set(x.o).size !== 4) throw new Error(`Invalid choices for ${x.id}`);
  if (!Number.isInteger(x.a) || x.a < 0 || x.a > 3) throw new Error(`Invalid answer index for ${x.id}`);
  return {
    id: x.id,
    originalId: x.id.replace(/^MCQ-/, ''),
    sourceId: meta.sourceId,
    originType: 'preexisting_qa_converted',
    aiGenerated: false,
    choicesGenerated: 'assistant-generated-distractors',
    sourceMode: 'Open-licensed source Q&A validated for IICA use and converted to a four-option MCQ; distractors were created for this tool.',
    sourceDomain: x.c,
    sourceTopic: x.c,
    category: x.c,
    subtopic: x.c,
    difficulty: x.d,
    difficultyLabel: ({ S: 'Simple', M: 'Medium', H: 'Hard' })[x.d] || x.d,
    question: x.q,
    options: x.o,
    answer: x.a,
    explanation: 'Validated source-Q&A proposition converted to MCQ for Director Mock India.',
    reference: 'Validated against the current Companies Act / SEBI / applicable securities-law framework in the 16 September 2026 source audit.',
    examEligible: true,
    validationRequired: false,
    reviewed: 'validated-and-converted-2026-09-16',
    qualityStatus: 'Validated source Q&A converted to MCQ',
    qualityIssues: '',
    needsCurrentnessReview: false,
    sourceLicense: meta.sourceLicense,
    sourceUrl: meta.sourceUrl,
    validatedAt: '2026-09-16'
  };
});
