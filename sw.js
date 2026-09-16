const CACHE='director-mock-v7-direct-only';
const ASSETS=['./','index.html','styles.css','app.js','data/open_questions.js','data/questions.js','data/openbank-loader.js','data/bank_manifest.json','manifest.json','icons/icon-192.png','icons/icon-512.png','SOURCES.md','QUESTION_BANK_LICENSE.md','AUDIT_SUMMARY.md'];
self.addEventListener('install',event=>{
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));
});
self.addEventListener('activate',event=>{
  event.waitUntil(Promise.all([
    self.clients.claim(),
    caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key))))
  ]));
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  if(new URL(event.request.url).origin!==self.location.origin) return;
  event.respondWith(caches.match(event.request).then(cached=>cached||fetch(event.request).then(response=>{
    const copy=response.clone();
    caches.open(CACHE).then(cache=>cache.put(event.request,copy));
    return response;
  })));
});
