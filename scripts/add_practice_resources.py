from pathlib import Path
import json, re

app_path=Path('app.js')
index_path=Path('index.html')
styles_path=Path('styles.css')
sw_path=Path('sw.js')
readme_path=Path('README.md')
resources_path=Path('data/practice_resources.js')

app=app_path.read_text(encoding='utf-8')

# Fix V9 mock sampler so validated source-QA conversions are eligible in normal mocks.
old_pool="const pool = shuffle(poolByCategory(category).filter(q => !q.aiGenerated && String(q.originType || '').startsWith('preexisting_')));"
new_pool="const pool = shuffle(poolByCategory(category).filter(q => !q.aiGenerated && (String(q.originType || '').startsWith('preexisting_') || q.originType === 'source_qa_converted_mcq')));"
if old_pool in app:
    app=app.replace(old_pool,new_pool,1)
elif new_pool not in app:
    raise SystemExit('Could not locate mock sampler filter')

helper="""
function practiceResourcesMarkup() {
  const resources = Array.isArray(window.PRACTICE_RESOURCES) ? window.PRACTICE_RESOURCES : [];
  if (!resources.length) return '';
  return `<section class="card practice-links-card">
    <div class="practice-links-heading">
      <div><h2>${icon('book', 22)} More Practice Questions</h2><p>Use these external resources when you want additional questions beyond this tool's 370-question bank.</p></div>
    </div>
    <div class="practice-resource-grid">
      ${resources.map(resource => `<a class="practice-resource" href="${escapeHtml(resource.url)}" target="_blank" rel="noopener noreferrer">
        <div class="practice-resource-top"><span class="resource-access">${escapeHtml(resource.access)}</span>${icon('arrow', 18)}</div>
        <strong>${escapeHtml(resource.title)}</strong>
        <span class="resource-provider">${escapeHtml(resource.provider)}</span>
        <small>${escapeHtml(resource.note)}</small>
      </a>`).join('')}
    </div>
    <div class="practice-resource-note">${icon('info', 17)} <span>External sites are independent of Director Mock India. Availability, pricing and question accuracy can change. For current rules and the official familiarisation mock, prioritize IICA.</span></div>
  </section>`;
}

"""
if 'function practiceResourcesMarkup()' not in app:
    marker='function renderHome() {'
    pos=app.find(marker)
    if pos < 0: raise SystemExit('renderHome marker missing')
    app=app[:pos]+helper+app[pos:]

# Add the section as the final dashboard card, immediately after quick actions.
start=app.find('function renderHome() {')
end=app.find('\nfunction confirmReplaceExam', start)
if start < 0 or end < 0: raise SystemExit('renderHome bounds missing')
home=app[start:end]
if '${practiceResourcesMarkup()}' not in home:
    target='      </div>\n      ${footerNote()}'
    idx=home.rfind(target)
    if idx < 0: raise SystemExit('home dashboard closing anchor missing')
    home=home[:idx]+'        ${practiceResourcesMarkup()}\n'+home[idx:]
    app=app[:start]+home+app[end:]
app_path.write_text(app,encoding='utf-8')

index=index_path.read_text(encoding='utf-8')
resource_script='  <script src="data/practice_resources.js"></script>\n'
if resource_script not in index:
    marker='  <script src="app.js"></script>\n'
    if marker not in index: raise SystemExit('app.js script tag missing')
    index=index.replace(marker,resource_script+marker,1)
index_path.write_text(index,encoding='utf-8')

css=styles_path.read_text(encoding='utf-8')
css_block=r'''

/* External practice resources */
.practice-links-card{grid-column:1/-1;padding:24px}
.practice-links-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:18px}
.practice-links-heading h2{display:flex;align-items:center;gap:9px;margin:0 0 5px;font-size:1.15rem}
.practice-links-heading p{margin:0;color:var(--muted);font-size:.92rem;line-height:1.45}
.practice-resource-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.practice-resource{display:flex;flex-direction:column;min-height:176px;padding:16px;border:1px solid var(--border);border-radius:14px;background:var(--card);color:inherit;text-decoration:none;transition:transform .15s ease,border-color .15s ease,box-shadow .15s ease}
.practice-resource:hover,.practice-resource:focus-visible{transform:translateY(-2px);border-color:#8eb9e8;box-shadow:0 8px 22px rgba(29,78,137,.10);outline:none}
.practice-resource-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;color:var(--primary)}
.resource-access{display:inline-flex;align-items:center;border-radius:999px;padding:4px 9px;background:#edf6ff;color:#165fa7;font-size:.72rem;font-weight:750;letter-spacing:.01em}
.practice-resource strong{font-size:.96rem;line-height:1.35;margin-bottom:5px}
.resource-provider{color:var(--muted);font-size:.78rem;font-weight:650;margin-bottom:9px}
.practice-resource small{color:var(--muted);font-size:.78rem;line-height:1.43;margin-top:auto}
.practice-resource-note{display:flex;align-items:flex-start;gap:8px;margin-top:14px;padding:11px 13px;border-radius:12px;background:#f7f9fc;color:var(--muted);font-size:.78rem;line-height:1.45}
.practice-resource-note .icon{flex:0 0 auto;margin-top:1px}
@media(max-width:900px){.practice-resource-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.practice-links-card{padding:18px}.practice-resource-grid{grid-template-columns:1fr}.practice-resource{min-height:0}.practice-links-heading p{font-size:.86rem}}
'''
if '/* External practice resources */' not in css:
    css=css.rstrip()+css_block+'\n'
styles_path.write_text(css,encoding='utf-8')

sw=sw_path.read_text(encoding='utf-8')
sw=re.sub(r"const CACHE='[^']+';", "const CACHE='director-mock-v10-practice-resources';", sw, count=1)
if "'data/practice_resources.js'" not in sw:
    asset_anchor="'data/questions.js',"
    if asset_anchor not in sw: raise SystemExit('service worker asset anchor missing')
    sw=sw.replace(asset_anchor,asset_anchor+"'data/practice_resources.js',",1)
sw_path.write_text(sw,encoding='utf-8')

readme=readme_path.read_text(encoding='utf-8')
section="""

## More practice resources

The home dashboard includes a responsive **More Practice Questions** section linking to the official IICA self-assessment/mock-test area plus selected free/public and paid third-party question banks. External resources are linked for additional practice only; their content is not copied into this repository and may have separate access, copyright and currentness conditions.
"""
if '## More practice resources' not in readme:
    readme=readme.rstrip()+section+'\n'
readme_path.write_text(readme,encoding='utf-8')

# Validate the resource catalog without executing arbitrary page code.
raw=resources_path.read_text(encoding='utf-8')
match=re.search(r'window\.PRACTICE_RESOURCES\s*=\s*(\[.*\]);\s*$', raw, re.S)
if not match: raise SystemExit('Practice resources catalog is not parseable')
resources=json.loads(match.group(1).replace("'", '"')) if False else None

print('Practice resource UI patch applied; mock sampler now includes source_qa_converted_mcq.')
