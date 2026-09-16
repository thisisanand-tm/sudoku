from pathlib import Path
import re

index_path=Path('index.html')
sw_path=Path('sw.js')
readme_path=Path('README.md')

index=index_path.read_text(encoding='utf-8')
script='  <script src="pwa-update.js"></script>\n'
if script not in index:
    marker='  <script src="app.js"></script>\n'
    if marker not in index: raise SystemExit('app.js marker missing')
    index=index.replace(marker, marker+script, 1)
index_path.write_text(index,encoding='utf-8')

sw=sw_path.read_text(encoding='utf-8')
sw=re.sub(r"const CACHE='[^']+';", "const CACHE='director-mock-v11-auto-update';", sw, count=1)
if "'pwa-update.js'" not in sw:
    sw=sw.replace("'app.js',", "'app.js','pwa-update.js',",1)

# Replace the cache-first fetch handler with online-first navigation and
# network-first same-origin assets. Offline fallback remains available.
start=sw.find("self.addEventListener('fetch'")
if start < 0: raise SystemExit('fetch handler missing')
sw=sw[:start]+"""self.addEventListener('message',event=>{
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
"""
sw_path.write_text(sw,encoding='utf-8')

readme=readme_path.read_text(encoding='utf-8')
section="""

## Automatic updates

The PWA explicitly checks for a new service worker on load, when the browser tab becomes visible/focused, and periodically while open. When a newer deployed worker takes control, an already-controlled page reloads itself once automatically. First-time service-worker installation does not force an unnecessary reload. Navigations use a network-first strategy with an offline cache fallback so ordinary refreshes prefer the latest deployed page when online.
"""
if '## Automatic updates' not in readme:
    readme=readme.rstrip()+section+'\n'
readme_path.write_text(readme,encoding='utf-8')
print('PWA automatic update behavior applied.')
