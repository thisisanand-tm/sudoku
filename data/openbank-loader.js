'use strict';
(() => {
  const frozen = Array.isArray(window.OPEN_QUESTION_BANK) ? window.OPEN_QUESTION_BANK : [];
  const manifest = window.OPEN_BANK_MANIFEST || {};
  window.OPEN_BANK_STATUS = {
    state: frozen.length ? 'ready' : 'unavailable',
    preexistingCount: frozen.length,
    corpusCount: frozen.length,
    directRelevantSourceRows: Number(manifest.directRelevantSourceRows || frozen.length),
    duplicateDirectStemsRemoved: Number(manifest.duplicateDirectStemsRemoved || 0),
    validationRequiredCount: Number(manifest.validationRequiredCount || 0),
    sourceQualityPassCount: Number(manifest.sourceQualityPassCount || 0),
    aiCount: 0,
    lastSync: manifest.generatedAt || null,
    error: frozen.length ? null : 'The bundled direct-relevance question bank could not be loaded.',
    manifest
  };
  window.syncOpenBank = async () => window.OPEN_BANK_STATUS;
  window.OPEN_BANK_READY = Promise.resolve(window.OPEN_BANK_STATUS);
})();
