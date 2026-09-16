'use strict';
(() => {
  const frozen = Array.isArray(window.QUESTION_BANK) ? window.QUESTION_BANK : [];
  const manifest = window.OPEN_BANK_MANIFEST || {};
  window.OPEN_BANK_STATUS = {
    state: frozen.length ? 'ready' : 'unavailable',
    preexistingCount: frozen.length,
    corpusCount: frozen.length,
    bhashaActiveCount: Number(manifest.bhashaActiveCount || 0),
    nptelImportedCount: Number(manifest.nptelImportedCount || 0),
    retiredAfterValidationCount: Number(manifest.retiredAfterValidationCount || 0),
    validationRequiredCount: Number(manifest.validationRequiredCount || 0),
    sourceQualityPassCount: Number(manifest.sourceQualityPassCount || frozen.length),
    aiCount: Number(manifest.aiQuestionCount || 0),
    lastSync: manifest.generatedAt || null,
    error: frozen.length ? null : 'The bundled sourced question bank could not be loaded.',
    manifest
  };
  window.syncOpenBank = async () => window.OPEN_BANK_STATUS;
  window.OPEN_BANK_READY = Promise.resolve(window.OPEN_BANK_STATUS);
})();
