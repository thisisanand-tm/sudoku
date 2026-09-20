'use strict';
const CACHE_PREFIX = 'sudoku-';
const CACHE = 'sudoku-restored-v4-20260920';
const ASSETS = ['./', 'index.html', 'sudoku-pwa.js', 'manifest.webmanifest', 'icon-512.png'];
const ROOT = new URL(self.registration.scope);
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => (key.startsWith(CACHE_PREFIX) && key !== CACHE) || key.startsWith('director-mock-')).map(key => caches.delete(key)));
    // Claim clients without awaiting a navigation that needs this activation to finish.
    await self.clients.claim();
  })());
});
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== ROOT.origin || !url.pathname.startsWith(ROOT.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const response = await fetch(event.request);
      if (response.ok) await cache.put(event.request, response.clone());
      return response;
    } catch (error) {
      const saved = await cache.match(event.request);
      if (saved) return saved;
      if (event.request.mode === 'navigate') {
        const home = await cache.match(new URL('index.html', ROOT).href);
        if (home) return home;
      }
      return Response.error();
    }
  })());
});
