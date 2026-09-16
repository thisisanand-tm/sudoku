const CACHE='director-mock-v11-auto-update';
const ASSETS=['./','index.html','styles.css','app.js','pwa-update.js','data/open_questions.js','data/nptel_questions.js','data/source_qa_compact_loader.js','data/source_qa_22.js','data/source_qa_21.js','data/source_qa_20.js','data/source_qa_19.js','data/source_qa_18.js','data/source_qa_17.js','data/source_qa_16.js','data/source_qa_15.js','data/source_qa_14.js','data/source_qa_13.js','data/source_qa_12.js','data/source_qa_11.js','data/source_qa_10.js','data/source_qa_09.js','data/source_qa_08.js','data/source_qa_07.js','data/source_qa_06.js','data/source_qa_05.js','data/source_qa_04.js','data/source_qa_03.js','data/source_qa_02.js','data/source_qa_01.js','data/questions.js','data/practice_resources.js','data/openbank-loader.js','data/bank_manifest.json','data/retired_questions.json','manifest.json','icons/icon-192.png','icons/icon-512.png','SOURCES.md','QUESTION_BANK_LICENSE.md','AUDIT_SUMMARY.md'];
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
self.addEventListener('message',event=>{
  if(event.data&&event.data.type==='SKIP_WAITING') self.skipWaiting();
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin) return;

  if(event.request.mode==='navigate'){
    event.respondWith(fetch(event.request).then(response=>{
      const copy=response.clone();
      caches.open(CACHE).then(cache=>cache.put('./',copy));
      return response;
    }).catch(()=>caches.match(event.request).then(cached=>cached||caches.match('./'))));
    return;
  }

  event.respondWith(fetch(event.request).then(response=>{
    if(response&&response.ok){
      const copy=response.clone();
      caches.open(CACHE).then(cache=>cache.put(event.request,copy));
    }
    return response;
  }).catch(()=>caches.match(event.request)));
});
