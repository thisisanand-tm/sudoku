'use strict';

(() => {
  if (!('serviceWorker' in navigator)) return;

  const hadControllerAtLoad = Boolean(navigator.serviceWorker.controller);
  let reloading = false;
  let registration = null;

  function reloadForNewVersion() {
    if (!hadControllerAtLoad || reloading) return;
    reloading = true;
    window.location.reload();
  }

  navigator.serviceWorker.addEventListener('controllerchange', reloadForNewVersion);

  async function checkForUpdate() {
    if (!registration) return;
    try {
      await registration.update();
    } catch (error) {
      console.debug('Service-worker update check skipped:', error);
    }
  }

  window.addEventListener('load', async () => {
    try {
      registration = await navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' });
      await checkForUpdate();

      if (registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }

      registration.addEventListener('updatefound', () => {
        const worker = registration.installing;
        if (!worker) return;
        worker.addEventListener('statechange', () => {
          if (worker.state === 'installed' && navigator.serviceWorker.controller) {
            worker.postMessage({ type: 'SKIP_WAITING' });
          }
        });
      });
    } catch (error) {
      console.warn('Service worker registration failed:', error);
    }
  });

  window.addEventListener('focus', checkForUpdate);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForUpdate();
  });

  window.setInterval(checkForUpdate, 5 * 60 * 1000);
})();
