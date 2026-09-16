'use strict';

const EXAM_CONFIG = {
  questionCount: 50,
  durationMinutes: 75,
  passPercent: 50,
  practiceCount: 20,
  categoryTargets: {
    'Companies Law': 30,
    'Securities Law': 10,
    'Basic Accountancy': 6,
    'Corporate Governance': 4
  },
  legalReviewDate: '16 September 2026'
};

const STORAGE = {
  history: 'directorMock.history.v2',
  legacyHistory: 'directorMock.history.v1',
  active: 'directorMock.active.v2',
  legacyActive: 'directorMock.active.v1'
};

const app = document.getElementById('app');
let timerId = null;
let state = null;
let currentView = 'home';

function shuffle(input) {
  const a = [...input];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

function sourceFor(question) {
  if (!question) return null;
  if (question.source && typeof question.source === 'object') return question.source;
  if (question.sourceId && typeof SOURCE_CATALOG !== 'undefined') return SOURCE_CATALOG[question.sourceId] || null;
  return null;
}

function difficultyLabel(code) {
  return ({ S: 'Simple', M: 'Medium', H: 'Hard', easy: 'Simple', medium: 'Medium', hard: 'Hard' })[code] || code || 'Unrated';
}

function difficultyBadge(question) {
  const code = String(question?.difficulty || '?').toUpperCase().slice(0, 1);
  const cls = ['S','M','H'].includes(code) ? code.toLowerCase() : 'legacy';
  return `<span class="difficulty-badge difficulty-${cls}" title="${escapeHtml(difficultyLabel(question?.difficulty))}">${escapeHtml(code)}</span>`;
}

function sourceMarkup(question, full = false) {
  const source = sourceFor(question);
  const type = question?.originType || (question?.aiGenerated ? 'ai_generated' : 'legacy');
  const typeLabel = type === 'preexisting_verbatim_mcq' ? 'Pre-existing MCQ' : type === 'preexisting_corrected_mcq' ? 'Pre-existing MCQ · source defect corrected' : type === 'preexisting_qa_converted' ? 'Pre-existing QA → MCQ' : type === 'ai_generated' ? 'AI-generated' : 'Legacy question';
  const aiLabel = question?.aiGenerated ? 'AI: Yes' : 'AI: No';
  const typeBadge = `<span class="origin-pill origin-${escapeHtml(type)}">${escapeHtml(typeLabel)}</span><span class="origin-pill ${question?.aiGenerated ? 'origin-ai' : 'origin-human'}">${aiLabel}</span>`;
  if (!source) return `<div class="source-line legacy-source">${typeBadge} <span>Source metadata unavailable.</span></div>`;
  const sourceName = escapeHtml(source.shortTitle || source.title || 'Source');
  const sourceItem = source.url ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${sourceName}</a>` : `<strong>${sourceName}</strong>`;
  const license = source.license ? `<a class="license-pill" href="${escapeHtml(source.licenseUrl || source.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.license)}</a>` : '';
  const note = full ? `<div class="source-provenance">${source.author ? `Attribution: ${escapeHtml(source.author)} · ` : ''}${escapeHtml(question.sourceMode || source.provenance || '')}${question.choicesGenerated ? ` · Choices: ${escapeHtml(question.choicesGenerated)}` : ''}${question.originalId ? ` · Original ID: ${escapeHtml(question.originalId)}` : ''}${question.jurisdiction ? ` · Jurisdiction: ${escapeHtml(question.jurisdiction)}` : ''}${question.qualityStatus ? ` · Quality: ${escapeHtml(question.qualityStatus)}` : ''}</div>` : '';
  return `<div class="source-line">${typeBadge}<span>Source:</span> ${sourceItem} ${license}${note}</div>`;
}

function findBankQuestion(id) {
  return QUESTION_BANK.find(q => q.id === id) || QUESTION_BANK.find(q => q.id === `${id}-1`) || null;
}

function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
function average(values) { return values.length ? values.reduce((sum, v) => sum + v, 0) / values.length : 0; }

function readJson(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); }
  catch { return fallback; }
}

function normaliseHistoryItem(item) {
  return {
    ...item,
    kind: item.kind || 'mock',
    total: Number(item.total || EXAM_CONFIG.questionCount),
    score: Number(item.score || 0),
    percent: Number(item.percent || 0),
    passed: typeof item.passed === 'boolean' ? item.passed : Number(item.percent || 0) >= EXAM_CONFIG.passPercent,
    legacy: Boolean(item.legacy || (!item.topics && !item.questionResults))
  };
}

function readHistory() {
  const current = readJson(STORAGE.history, null);
  if (Array.isArray(current)) return current.map(normaliseHistoryItem);

  const legacy = readJson(STORAGE.legacyHistory, []);
  if (Array.isArray(legacy) && legacy.length) {
    const migrated = legacy.map(item => normaliseHistoryItem({ ...item, legacy: true, kind: 'mock' }));
    writeHistory(migrated);
    return migrated;
  }
  return [];
}

function writeHistory(items) {
  localStorage.setItem(STORAGE.history, JSON.stringify(items.slice(0, 30)));
}

function saveActive() {
  if (state?.status === 'active') localStorage.setItem(STORAGE.active, JSON.stringify(state));
}

function clearActive() {
  localStorage.removeItem(STORAGE.active);
  localStorage.removeItem(STORAGE.legacyActive);
}

function readActive() {
  const keys = [STORAGE.active, STORAGE.legacyActive];
  for (const key of keys) {
    const s = readJson(key, null);
    if (!s || s.status !== 'active' || !Array.isArray(s.questions)) continue;
    s.kind ||= 'mock';
    if (s.kind === 'mock' && !s.deadline) s.deadline = s.startedAt + EXAM_CONFIG.durationMinutes * 60 * 1000;
    return s;
  }
  return null;
}

function formatTime(totalSeconds) {
  const n = Math.max(0, Math.round(totalSeconds));
  const m = Math.floor(n / 60), s = n % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatDuration(totalSeconds) {
  const n = Math.max(0, Math.round(totalSeconds));
  const m = Math.floor(n / 60);
  const s = n % 60;
  return m ? `${m}m ${s ? `${s}s` : ''}`.trim() : `${s}s`;
}

function formatDate(iso) {
  return new Intl.DateTimeFormat(undefined, { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(iso));
}

function formatShortDate(iso) {
  return new Intl.DateTimeFormat(undefined, { day: '2-digit', month: 'short' }).format(new Date(iso));
}

function todayLabel() {
  return new Intl.DateTimeFormat(undefined, { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date());
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning!';
  if (hour < 18) return 'Good afternoon!';
  return 'Good evening!';
}

function icon(name, size = 22) {
  const icons = {
    building: '<path d="M3 10h18M5 10v8m4-8v8m6-8v8m4-8v8M2 21h20M4 7l8-4 8 4H4Z"/>',
    home: '<path d="m3 11 9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-9Z"/>',
    chart: '<path d="M4 20V10m6 10V4m6 16v-7m4 7H2"/>',
    book: '<path d="M4 5a3 3 0 0 1 3-3h5v18H7a3 3 0 0 0-3 3V5Zm16 0a3 3 0 0 0-3-3h-5v18h5a3 3 0 0 1 3 3V5Z"/>',
    gear: '<path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.1A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.1A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.1A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.17.36.27.75.3 1.15H21v4h-1.3c-.03.3-.13.58-.3.85Z"/>',
    play: '<path d="m8 5 11 7-11 7V5Z"/>',
    target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 12 20 4M17 4h3v3"/>',
    file: '<path d="M6 2h8l4 4v16H6V2Z"/><path d="M14 2v5h5M9 12h6M9 16h6"/>',
    arrow: '<path d="m9 18 6-6-6-6"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    warning: '<path d="M12 3 2.5 20h19L12 3Z"/><path d="M12 9v5M12 17h.01"/>',
    trend: '<path d="m3 17 6-6 4 4 8-9M16 6h5v5"/>'
  };
  return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.info}</svg>`;
}

function navButton(view, label, iconName, active) {
  return `<button class="nav-item ${active === view ? 'active' : ''}" data-view="${view}">${icon(iconName, 21)}<span>${label}</span></button>`;
}

function appHeader(active = 'home', extra = '') {
  return `<header class="topbar"><div class="topbar-inner">
    <button class="brand-button" data-view="home" aria-label="Director Mock India home">
      <span class="brand-mark">${icon('building', 28)}</span>
      <span><strong>Director Mock India</strong><small>Practice. Prepare. Perform.</small></span>
    </button>
    <nav class="desktop-nav" aria-label="Primary navigation">
      ${navButton('home', 'Home', 'home', active)}
      ${navButton('history', 'History', 'chart', active)}
      ${navButton('practice', 'Practice', 'book', active)}
      ${navButton('settings', 'Settings', 'gear', active)}
    </nav>
    ${extra || `<button class="icon-button mobile-settings" data-view="settings" aria-label="Settings">${icon('gear', 23)}</button>`}
  </div></header>`;
}

function bottomNav(active = 'home') {
  return `<nav class="bottom-nav" aria-label="Primary navigation">
    ${navButton('home', 'Home', 'home', active)}
    ${navButton('history', 'History', 'chart', active)}
    ${navButton('practice', 'Practice', 'book', active)}
    ${navButton('settings', 'Settings', 'gear', active)}
  </nav>`;
}

function footerNote() {
  return `<div class="footer-note">Unofficial educational preparation tool. Not affiliated with or endorsed by IICA, MCA or SEBI. The active mock bank uses openly licensed sourced material; no AI-authored question stems are served. Source-QA items converted to MCQ use assistant-generated distractors and are labelled accordingly. Every item displays provenance, licence and S/M/H difficulty. Active items were reviewed for current-law suitability as of the build review date. No IICA live/proctored exam questions are reproduced. Regulations can change. Build review date ${escapeHtml(EXAM_CONFIG.legalReviewDate)}.</div>`;
}

function bindNavigation() {
  document.querySelectorAll('[data-view]').forEach(button => {
    button.onclick = () => navigate(button.dataset.view);
  });
}

function navigate(view) {
  currentView = view;
  if (view === 'history') return renderHistory();
  if (view === 'practice') return renderPractice();
  if (view === 'settings') return renderSettings();
  return renderHome();
}

function eligibleQuestion(q) { return q.examEligible !== false; }
function poolByCategory(category) { return QUESTION_BANK.filter(q => eligibleQuestion(q) && q.category === category); }
function poolByCategoryDifficulty(category, difficulty) { return QUESTION_BANK.filter(q => eligibleQuestion(q) && q.category === category && q.difficulty === difficulty); }
function originCounts() {
  const eligible = QUESTION_BANK.filter(eligibleQuestion);
  return {
    total: eligible.length,
    preexisting: eligible.filter(q => !q.aiGenerated && String(q.originType || '').startsWith('preexisting_')).length,
    ai: eligible.filter(q => q.aiGenerated || q.originType === 'ai_generated').length,
    verbatim: eligible.filter(q => q.originType === 'preexisting_verbatim_mcq').length,
    converted: eligible.filter(q => q.originType === 'preexisting_qa_converted').length
  };
}

function prepareQuestion(q) {
  const tagged = q.options.map((text, index) => ({ text, isCorrect: index === q.answer }));
  const mixed = shuffle(tagged);
  return {
    id: q.id,
    category: q.category,
    subtopic: q.subtopic,
    difficulty: q.difficulty,
    difficultyLabel: q.difficultyLabel || difficultyLabel(q.difficulty),
    sourceId: q.sourceId || null,
    source: sourceFor(q),
    sourceMode: q.sourceMode || null,
    originType: q.originType || null,
    aiGenerated: Boolean(q.aiGenerated),
    choicesGenerated: q.choicesGenerated || null,
    originalId: q.originalId || null,
    reviewed: q.reviewed || null,
    question: q.question,
    options: mixed.map(x => x.text),
    correctIndex: mixed.findIndex(x => x.isCorrect),
    explanation: q.explanation,
    reference: q.reference,
    selectedIndex: null,
    flagged: false
  };
}

async function createMock() {
  if (window.OPEN_BANK_READY) await window.OPEN_BANK_READY;
  const picked = [];
  for (const [category, count] of Object.entries(EXAM_CONFIG.categoryTargets)) {
    const pool = shuffle(poolByCategory(category).filter(q => !q.aiGenerated && String(q.originType || '').startsWith('preexisting_')));
    if (pool.length < count) throw new Error(`Not enough direct-relevance questions in ${category}: need ${count}, have ${pool.length}.`);
    picked.push(...pool.slice(0, count));
  }
  startExamState(shuffle(picked).map(prepareQuestion), 'mock');
}


function aggregateSubjects(history = readHistory()) {
  const map = {};
  history.filter(item => item.kind === 'mock' && Array.isArray(item.topics)).forEach(item => {
    item.topics.forEach(t => {
      map[t.category] ||= { category: t.category, correct: 0, total: 0 };
      map[t.category].correct += Number(t.correct || 0);
      map[t.category].total += Number(t.total || 0);
    });
  });
  return Object.values(map).map(x => ({ ...x, percent: x.total ? Math.round(x.correct / x.total * 100) : 0 }));
}

function aggregateMistakes(history = readHistory()) {
  const misses = new Map();
  history.filter(item => item.kind === 'mock' && Array.isArray(item.questionResults)).forEach(item => {
    item.questionResults.forEach(r => {
      if (r.wasCorrect) return;
      const key = `${r.category}::${r.subtopic}`;
      const existing = misses.get(key) || { category: r.category, subtopic: r.subtopic, misses: 0 };
      existing.misses += 1;
      misses.set(key, existing);
    });
  });
  return [...misses.values()].sort((a, b) => b.misses - a.misses);
}

function weakestCategory(history = readHistory()) {
  const subjects = aggregateSubjects(history).sort((a, b) => a.percent - b.percent);
  return subjects[0]?.category || null;
}

async function createPractice() {
  if (window.OPEN_BANK_READY) await window.OPEN_BANK_READY;
  const history = readHistory();
  const weak = weakestCategory(history);
  let picked = [];
  if (weak) {
    const primary = shuffle(poolByCategory(weak));
    picked.push(...primary.slice(0, Math.min(EXAM_CONFIG.practiceCount, primary.length)));
  }
  if (picked.length < EXAM_CONFIG.practiceCount) {
    const used = new Set(picked.map(q => q.id));
    const rest = shuffle(QUESTION_BANK.filter(q => eligibleQuestion(q) && !used.has(q.id)));
    picked.push(...rest.slice(0, EXAM_CONFIG.practiceCount - picked.length));
  }
  startExamState(shuffle(picked).map(prepareQuestion), 'practice', weak);
}


async function startBankAction(kind) {
  try {
    if (kind === 'practice') await createPractice();
    else await createMock();
  } catch (error) {
    const message = String(error?.message || error || 'The sourced question bank is not ready.');
    showModal('Question bank not ready', message, [
      { label: 'Close', cls: 'btn-secondary', action: closeModal },
      { label: 'Refresh sourced bank', cls: 'btn-primary', action: async () => { closeModal(); try { await window.syncOpenBank?.(); } finally { navigate(currentView); } } }
    ]);
  }
}

function startExamState(questions, kind, focusCategory = null) {
  const now = Date.now();
  state = {
    status: 'active',
    kind,
    focusCategory,
    questions,
    current: 0,
    startedAt: now,
    deadline: kind === 'mock' ? now + EXAM_CONFIG.durationMinutes * 60 * 1000 : null
  };
  saveActive();
  renderExam();
}

function mockHistory() { return readHistory().filter(item => item.kind === 'mock'); }

function dashboardMetrics(history = mockHistory()) {
  if (!history.length) return { count: 0, average: null, best: null, passes: 0, streak: 0, readiness: null, status: 'Start practicing', statusClass: 'neutral', last: null };
  const percents = history.map(h => h.percent);
  const overall = average(percents);
  const recent3 = average(history.slice(0, 3).map(h => h.percent));
  const readiness = Math.round(history.length >= 3 ? (0.7 * recent3 + 0.3 * overall) : overall);
  const streak = history.findIndex(h => !h.passed) === -1 ? history.length : history.findIndex(h => !h.passed);
  let status = 'Needs Practice', statusClass = 'bad';
  if (readiness >= 80) { status = 'Ready'; statusClass = 'good'; }
  else if (readiness >= 65) { status = 'Nearly Ready'; statusClass = 'warn'; }
  return {
    count: history.length,
    average: Math.round(overall),
    best: Math.max(...percents),
    passes: history.filter(h => h.passed).length,
    streak,
    readiness,
    status,
    statusClass,
    last: history[0]
  };
}

function trendChart(history) {
  const attempts = history.slice(0, 5).reverse();
  if (!attempts.length) return `<div class="empty-chart"><div class="empty-chart-line"></div><p>Complete a mock to start your score trend.</p></div>`;

  const width = 620, height = 210, padL = 42, padR = 18, padT = 28, padB = 48;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const x = i => attempts.length === 1 ? padL + plotW / 2 : padL + (i * plotW / (attempts.length - 1));
  const y = pct => padT + (100 - clamp(pct, 0, 100)) * plotH / 100;
  const points = attempts.map((a, i) => `${x(i)},${y(a.percent)}`).join(' ');
  const grid = [0, 50, 100].map(v => `<line x1="${padL}" y1="${y(v)}" x2="${width - padR}" y2="${y(v)}" class="chart-grid"/><text x="3" y="${y(v) + 4}" class="chart-axis">${v}%</text>`).join('');
  const dots = attempts.map((a, i) => `<g><circle cx="${x(i)}" cy="${y(a.percent)}" r="5.5" class="chart-dot"/><text x="${x(i)}" y="${Math.max(16, y(a.percent) - 13)}" text-anchor="middle" class="chart-score">${a.percent}%</text><text x="${x(i)}" y="${height - 25}" text-anchor="middle" class="chart-label">Test ${history.length - attempts.length + i + 1}</text><text x="${x(i)}" y="${height - 9}" text-anchor="middle" class="chart-date">${formatShortDate(a.finishedAt)}</text></g>`).join('');
  return `<div class="chart-scroll"><svg class="trend-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Score trend for the latest ${attempts.length} mock tests">${grid}<polyline points="${points}" class="chart-line"/>${dots}</svg></div>`;
}

function subjectIcon(category) {
  if (category === 'Companies Law') return 'CL';
  if (category === 'Securities Law') return 'SE';
  if (category === 'Basic Accountancy') return 'BA';
  return 'CG';
}

function subjectClass(category) {
  if (category === 'Companies Law') return 'blue';
  if (category === 'Corporate Governance') return 'purple';
  if (category === 'Basic Accountancy') return 'amber';
  return 'red';
}

function renderSubjectRows(history) {
  const subjects = aggregateSubjects(history).sort((a, b) => b.percent - a.percent);
  if (!subjects.length) return `<div class="empty-state compact"><strong>Topic analytics start with your next completed mock.</strong><span>Existing legacy scores still count toward overall score trends and averages.</span></div>`;
  return subjects.map(s => `<div class="subject-row">
    <span class="subject-icon ${subjectClass(s.category)}">${subjectIcon(s.category)}</span>
    <div class="subject-name">${escapeHtml(s.category)}<small>${s.correct}/${s.total} correct</small></div>
    <div class="subject-progress"><span class="${subjectClass(s.category)}" style="width:${s.percent}%"></span></div>
    <strong class="subject-score">${s.percent}%</strong>
  </div>`).join('');
}

function renderHome() {
  stopTimer();
  currentView = 'home';
  const history = mockHistory();
  const metrics = dashboardMetrics(history);
  const active = readActive();
  const subjects = aggregateSubjects(history).sort((a, b) => a.percent - b.percent);
  const weak = subjects[0];
  const latestFive = history.slice(0, 5);
  const trendDirection = latestFive.length >= 2 ? latestFive[0].percent - latestFive[latestFive.length - 1].percent : 0;
  const trendLabel = trendDirection > 2 ? 'Improving' : trendDirection < -2 ? 'Needs attention' : 'Stable';
  const bank = originCounts();
  const bankStatus = window.OPEN_BANK_STATUS || { state: 'loading', preexistingCount: bank.preexisting, aiCount: 0 };
  const bankReady = bankStatus.preexistingCount > 0;
  const validationCount = Number(bankStatus.validationRequiredCount || 0);
  const bankStatusHtml = `<div class="bank-status ${bankReady ? 'ready' : bankStatus.state === 'loading' ? 'loading' : 'partial'}"><span class="bank-dot"></span><strong>${bankStatus.state === 'loading' ? 'Loading sourced question bank…' : bankReady ? `${bankStatus.preexistingCount.toLocaleString()} unique direct-IICA questions ready` : 'Question bank unavailable'}</strong><span> · 0 AI-authored</span>${validationCount ? `<span> · ${validationCount} source answers/current-law items flagged for validation</span>` : ''}${bankStatus.error ? `<small>${escapeHtml(bankStatus.error)}</small>` : ''}</div>`;

  app.innerHTML = `<div class="app-shell dashboard-shell">
    ${appHeader('home')}
    <main class="dashboard-main">
      <div class="dashboard-grid">
        <section class="card readiness-card">
          <div class="readiness-heading-row"><div><h1>${greeting()}</h1><p>Here's your progress so far.</p></div><time>${todayLabel()}</time></div>
          <div class="readiness-content">
            <div class="readiness-primary">
              <div class="readiness-label">Exam Readiness <span class="info-tip" title="Training readiness = 70% of your last 3 mock average + 30% of your overall mock average. It is not a probability of passing.">${icon('info', 17)}</span></div>
              <div class="readiness-value">${metrics.readiness === null ? '—' : metrics.readiness + '%'}</div>
              <div class="progress-track"><span style="width:${metrics.readiness || 0}%"></span></div>
              <div class="readiness-status ${metrics.statusClass}">${metrics.statusClass === 'good' ? icon('check', 17) : metrics.statusClass === 'bad' ? icon('warning', 17) : icon('check', 17)} ${metrics.status}</div>
              <p class="readiness-note">${metrics.count ? (metrics.status === 'Ready' ? 'Keep your scores consistent before the real assessment.' : 'Keep practising to improve further.') : 'Complete your first mock to establish a baseline.'}</p>
            </div>
            <div class="readiness-stats">
              <div><span>Mocks completed</span><strong>${metrics.count}</strong></div>
              <div><span>Average score</span><strong>${metrics.average === null ? '—' : metrics.average + '%'}</strong></div>
              <div><span>Best score</span><strong>${metrics.best === null ? '—' : metrics.best + '%'}</strong></div>
              <div><span>Passes</span><strong>${metrics.count ? `${metrics.passes} / ${metrics.count}` : '—'}</strong></div>
              <div><span>Current streak</span><strong class="${metrics.streak ? 'positive' : ''}">${metrics.streak ? `${metrics.streak} Pass${metrics.streak === 1 ? '' : 'es'}` : '—'}</strong></div>
            </div>
          </div>
          ${bankStatusHtml}
          <div class="primary-actions">
            <button class="btn btn-primary btn-large" id="startExam">${icon('play', 21)} Start New Mock Test ${icon('arrow', 20)}</button>
            ${active ? `<button class="btn btn-secondary btn-large" id="resumeExam">Resume ${active.kind === 'practice' ? 'Practice' : 'Current Mock'}</button>` : ''}
          </div>
        </section>

        <section class="card trend-card">
          <div class="card-heading"><h2>Score Trend</h2><span class="trend-badge ${trendDirection < -2 ? 'down' : ''}">${icon('trend', 19)} ${trendLabel}</span></div>
          ${trendChart(history)}
        </section>

        <section class="card subject-card">
          <div class="card-heading"><h2>${icon('chart', 21)} Subject Performance</h2></div>
          <div class="subject-list">${renderSubjectRows(history)}</div>
          ${weak ? `<div class="priority-alert">${icon('warning', 22)}<div><strong>Priority area: ${escapeHtml(weak.category)}</strong><span>Focus here to improve your score.</span></div></div>` : ''}
        </section>

        <section class="quick-actions">
          <button class="action-card" id="practiceWeak">
            <span class="action-icon target">${icon('target', 27)}</span>
            <span><strong>Practice My Weak Areas</strong><small>${weak ? `${EXAM_CONFIG.practiceCount} questions focused on ${escapeHtml(weak.category)}` : `${EXAM_CONFIG.practiceCount} adaptive practice questions`}</small></span>
            ${icon('arrow', 22)}
          </button>
          <button class="action-card" id="reviewAttempts">
            <span class="action-icon file">${icon('file', 27)}</span>
            <span><strong>Review All Attempts</strong><small>See results, topics and explanations</small></span>
            ${icon('arrow', 22)}
          </button>
        </section>
      </div>
      ${footerNote()}
    </main>
    ${bottomNav('home')}
  </div>`;

  bindNavigation();
  document.getElementById('startExam').onclick = () => active ? confirmReplaceExam('mock') : startBankAction('mock');
  const resume = document.getElementById('resumeExam');
  if (resume) resume.onclick = () => {
    state = readActive();
    if (state.kind === 'mock' && state.deadline && Date.now() >= state.deadline) submitExam(true);
    else renderExam();
  };
  document.getElementById('practiceWeak').onclick = () => active ? confirmReplaceExam('practice') : startBankAction('practice');
  document.getElementById('reviewAttempts').onclick = renderHistory;
}

function confirmReplaceExam(nextKind) {
  showModal('Start a new session?', 'Your current unfinished session will be replaced.', [
    { label: 'Cancel', cls: 'btn-secondary', action: closeModal },
    { label: 'Start new', cls: 'btn-danger', action: () => { closeModal(); clearActive(); startBankAction(nextKind); } }
  ]);
}

function renderExam() {
  if (!state || state.status !== 'active') return renderHome();
  if (state.kind === 'mock' && state.deadline && Date.now() >= state.deadline) return submitExam(true);
  const q = state.questions[state.current];
  const answered = state.questions.filter(x => x.selectedIndex !== null).length;
  const flagged = state.questions.filter(x => x.flagged).length;
  const label = state.kind === 'practice' ? 'Weak-area practice' : '50-question mock';

  app.innerHTML = `<div class="app-shell exam-shell">
    ${appHeader('', `<span class="exam-header-pill">${escapeHtml(label)} · <span id="answeredCount">${answered}</span>/${state.questions.length} answered</span>`)}
    <main class="exam-main">
      <div class="exam-layout">
        <section class="card exam-card">
          <div class="exam-head">
            <div><div class="q-meta">Question ${state.current + 1} of ${state.questions.length}</div><div class="q-topic">${escapeHtml(q.category)} · ${escapeHtml(q.subtopic)} ${difficultyBadge(q)}</div>${sourceMarkup(q)}</div>
            <div class="timer ${state.kind === 'practice' ? 'untimed' : ''}" id="timer">${state.kind === 'practice' ? 'Untimed' : '--:--'}</div>
          </div>
          <div class="question">${escapeHtml(q.question)}</div>
          <div class="options">
            ${q.options.map((opt, i) => `<label class="option ${q.selectedIndex === i ? 'selected' : ''}">
              <input type="radio" name="answer" value="${i}" ${q.selectedIndex === i ? 'checked' : ''}/>
              <span class="option-letter">${String.fromCharCode(65 + i)}</span><span>${escapeHtml(opt)}</span>
            </label>`).join('')}
          </div>
          <div class="exam-footer">
            <label class="flag"><input type="checkbox" id="flagQuestion" ${q.flagged ? 'checked' : ''}/> Flag for review</label>
            <div class="actions exam-nav-actions">
              <button class="btn btn-secondary" id="prevBtn" ${state.current === 0 ? 'disabled' : ''}>Previous</button>
              <button class="btn btn-primary" id="nextBtn">${state.current === state.questions.length - 1 ? 'Review' : 'Next'}</button>
            </div>
          </div>
        </section>
        <aside class="card sidebar">
          <div class="sidebar-heading"><h2>Questions</h2><span>${answered}/${state.questions.length}</span></div>
          <div class="nav-grid">${state.questions.map((x, i) => `<button class="qnav ${i === state.current ? 'current' : ''} ${x.selectedIndex !== null ? 'answered' : ''} ${x.flagged ? 'flagged' : ''}" data-i="${i}">${i + 1}</button>`).join('')}</div>
          <div class="legend"><span><i class="dot green"></i>Answered</span><span><i class="dot orange"></i>Flagged</span><span><i class="dot"></i>Open</span></div>
          <div class="small sidebar-summary">${answered} answered · ${state.questions.length - answered} unanswered · ${flagged} flagged</div>
          <div class="actions stacked"><button class="btn btn-primary" id="submitBtn">Submit ${state.kind === 'practice' ? 'practice' : 'mock'}</button><button class="btn btn-secondary" id="exitBtn">Exit & resume later</button></div>
        </aside>
      </div>
    </main>
  </div>`;

  document.querySelectorAll('input[name="answer"]').forEach(el => el.onchange = e => {
    q.selectedIndex = Number(e.target.value); saveActive(); renderExam();
  });
  document.getElementById('flagQuestion').onchange = e => { q.flagged = e.target.checked; saveActive(); renderExam(); };
  document.querySelectorAll('.qnav').forEach(b => b.onclick = () => { state.current = Number(b.dataset.i); saveActive(); renderExam(); });
  document.getElementById('prevBtn').onclick = () => { if (state.current > 0) { state.current--; saveActive(); renderExam(); } };
  document.getElementById('nextBtn').onclick = () => { if (state.current < state.questions.length - 1) { state.current++; saveActive(); renderExam(); } else showReviewSubmit(); };
  document.getElementById('submitBtn').onclick = showReviewSubmit;
  document.getElementById('exitBtn').onclick = () => { saveActive(); renderHome(); };
  if (state.kind === 'mock') startTimer(); else stopTimer();
}

function showReviewSubmit() {
  const unanswered = state.questions.filter(q => q.selectedIndex === null).length;
  const flagged = state.questions.filter(q => q.flagged).length;
  showModal(`Submit this ${state.kind === 'practice' ? 'practice set' : 'mock'}?`, `${unanswered} unanswered question${unanswered === 1 ? '' : 's'} and ${flagged} flagged question${flagged === 1 ? '' : 's'} remain. You cannot change answers after submission.`, [
    { label: 'Keep working', cls: 'btn-secondary', action: closeModal },
    { label: 'Submit', cls: 'btn-primary', action: () => { closeModal(); submitExam(false); } }
  ]);
}

function calculateTopics(questions) {
  const map = {};
  questions.forEach(q => {
    map[q.category] ||= { category: q.category, correct: 0, total: 0 };
    map[q.category].total++;
    if (q.selectedIndex === q.correctIndex) map[q.category].correct++;
  });
  return Object.values(map).map(x => ({ ...x, percent: Math.round(x.correct / x.total * 100) }));
}

function questionResultSnapshot(questions) {
  return questions.map(q => ({
    id: q.id,
    category: q.category,
    subtopic: q.subtopic,
    difficulty: q.difficulty,
    sourceId: q.sourceId || null,
    selected: q.selectedIndex === null ? null : q.options[q.selectedIndex],
    correct: q.options[q.correctIndex],
    wasCorrect: q.selectedIndex === q.correctIndex
  }));
}

function submitExam(auto = false) {
  if (!state) return;
  stopTimer();
  const finishedAt = Date.now();
  const score = state.questions.reduce((n, q) => n + (q.selectedIndex === q.correctIndex ? 1 : 0), 0);
  const percent = Math.round((score / state.questions.length) * 100);
  const elapsedSeconds = state.kind === 'mock'
    ? Math.min(EXAM_CONFIG.durationMinutes * 60, Math.round((finishedAt - state.startedAt) / 1000))
    : Math.round((finishedAt - state.startedAt) / 1000);
  const result = {
    ...state,
    status: 'complete',
    finishedAt,
    autoSubmitted: auto,
    score,
    percent,
    passed: percent >= EXAM_CONFIG.passPercent,
    elapsedSeconds,
    topics: calculateTopics(state.questions)
  };

  if (state.kind === 'mock') {
    const history = readHistory();
    history.unshift({
      kind: 'mock',
      finishedAt: new Date(finishedAt).toISOString(),
      score,
      total: state.questions.length,
      percent,
      passed: result.passed,
      elapsedSeconds,
      timeUsed: formatTime(elapsedSeconds),
      topics: result.topics,
      questionResults: questionResultSnapshot(state.questions),
      legalReviewDate: EXAM_CONFIG.legalReviewDate
    });
    writeHistory(history);
  }

  clearActive();
  state = result;
  renderResults();
}

function topicBreakdown() { return calculateTopics(state.questions).sort((a, b) => a.percent - b.percent); }

function renderResults() {
  const topics = topicBreakdown();
  const wrongCount = state.questions.length - state.score;
  const isPractice = state.kind === 'practice';
  app.innerHTML = `<div class="app-shell results-shell">${appHeader('')}
    <main class="results-main">
      <div class="results-grid">
        <section class="card result-hero">
          ${state.autoSubmitted ? '<div class="notice">Time expired, so the mock was submitted automatically.</div>' : ''}
          <div class="result-kicker">${isPractice ? 'Practice result' : 'Mock exam result'}</div>
          <div class="score-ring" style="--pct:${state.percent}"><div class="score-content"><div class="score-big">${state.percent}%</div><div class="small">${state.score}/${state.questions.length}</div></div></div>
          <h1 class="${state.passed ? 'pass' : 'fail'}">${state.passed ? 'PASS' : 'NOT YET'}</h1>
          <div class="small result-meta">Time used ${formatDuration(state.elapsedSeconds)} · ${wrongCount} incorrect/unanswered</div>
          <div class="actions result-actions"><button class="btn btn-primary" id="newMock">New mock</button>${!isPractice ? '<button class="btn btn-secondary" id="practiceNext">Practice weak areas</button>' : ''}<button class="btn btn-secondary" id="homeBtn">Dashboard</button></div>
        </section>
        <section class="card result-topics">
          <h2>Performance by topic</h2>
          ${topics.map(t => `<div class="topic-row"><div><strong>${escapeHtml(t.category)}</strong><div class="small">${t.correct} of ${t.total} correct</div></div><div class="topic-bar"><span style="width:${t.percent}%"></span></div><strong class="${t.percent >= EXAM_CONFIG.passPercent ? 'pass' : 'fail'}">${t.percent}%</strong></div>`).join('')}
        </section>
        <section class="card answer-review">
          <div class="review-heading"><h2>Answer review</h2><button class="btn btn-secondary" id="wrongOnly">Show incorrect only</button></div>
          <div id="reviewList">${renderReviewItems(false)}</div>
        </section>
      </div>${footerNote()}
    </main>
  </div>`;
  bindNavigation();
  document.getElementById('newMock').onclick = createMock;
  document.getElementById('homeBtn').onclick = renderHome;
  const practiceNext = document.getElementById('practiceNext');
  if (practiceNext) practiceNext.onclick = createPractice;
  let wrongOnly = false;
  document.getElementById('wrongOnly').onclick = e => {
    wrongOnly = !wrongOnly;
    e.target.textContent = wrongOnly ? 'Show all' : 'Show incorrect only';
    document.getElementById('reviewList').innerHTML = renderReviewItems(wrongOnly);
  };
}

function renderReviewItems(wrongOnly) {
  const filtered = state.questions.map((q, i) => ({ q, i })).filter(({ q }) => !wrongOnly || q.selectedIndex !== q.correctIndex);
  if (!filtered.length) return '<p class="small">No incorrect answers — excellent work.</p>';
  return filtered.map(({ q, i }) => {
    const correct = q.selectedIndex === q.correctIndex;
    const yours = q.selectedIndex === null ? 'Unanswered' : `${String.fromCharCode(65 + q.selectedIndex)}. ${q.options[q.selectedIndex]}`;
    const right = `${String.fromCharCode(65 + q.correctIndex)}. ${q.options[q.correctIndex]}`;
    return `<article class="review-item">
      <div class="q-meta">Question ${i + 1} · ${escapeHtml(q.category)} · ${escapeHtml(q.subtopic)} ${difficultyBadge(q)}</div>
      ${sourceMarkup(q, true)}
      <div class="review-question">${escapeHtml(q.question)}</div>
      <span class="answer-tag ${correct ? 'correct' : 'wrong'}">Your answer: ${escapeHtml(yours)}</span>
      ${correct ? '' : `<span class="answer-tag correct">Correct: ${escapeHtml(right)}</span>`}
      <div class="review-explanation">${escapeHtml(q.explanation)}</div>
      <div class="reference">Indian-law / concept reference: ${escapeHtml(q.reference)}</div>
    </article>`;
  }).join('');
}

function renderHistory() {
  stopTimer();
  currentView = 'history';
  const history = mockHistory();
  const metrics = dashboardMetrics(history);
  const rows = history.map((h, index) => `<button class="attempt-card" data-attempt-index="${index}">
    <span class="attempt-score ${h.passed ? 'pass-bg' : 'fail-bg'}">${h.percent}%</span>
    <span class="attempt-main"><strong>Mock ${history.length - index}</strong><small>${formatDate(h.finishedAt)} · ${h.score}/${h.total} correct · ${h.timeUsed || (h.elapsedSeconds ? formatDuration(h.elapsedSeconds) : 'time not recorded')}</small></span>
    <span class="attempt-result ${h.passed ? 'pass' : 'fail'}">${h.passed ? 'PASS' : 'NOT YET'}</span>
    ${icon('arrow', 21)}
  </button>`).join('');

  app.innerHTML = `<div class="app-shell dashboard-shell">${appHeader('history')}
    <main class="dashboard-main">
      <section class="page-heading"><div><div class="eyebrow">Performance history</div><h1>Your mock attempts</h1><p>Review progress and reopen detailed explanations from recent tests.</p></div><button class="btn btn-primary" id="historyNewMock">Start New Mock</button></section>
      <div class="summary-strip">
        <div><span>Mocks</span><strong>${metrics.count}</strong></div><div><span>Average</span><strong>${metrics.average === null ? '—' : metrics.average + '%'}</strong></div><div><span>Best</span><strong>${metrics.best === null ? '—' : metrics.best + '%'}</strong></div><div><span>Passes</span><strong>${metrics.count ? `${metrics.passes}/${metrics.count}` : '—'}</strong></div>
      </div>
      <section class="card history-list-card"><div class="card-heading"><h2>All attempts</h2><span class="small">Stored only on this device</span></div>${history.length ? `<div class="attempt-list">${rows}</div>` : '<div class="empty-state"><strong>No completed mocks yet.</strong><span>Your results will appear here after your first full mock.</span></div>'}</section>
      ${footerNote()}
    </main>${bottomNav('history')}
  </div>`;
  bindNavigation();
  document.getElementById('historyNewMock').onclick = () => readActive() ? confirmReplaceExam('mock') : startBankAction('mock');
  document.querySelectorAll('[data-attempt-index]').forEach(btn => btn.onclick = () => renderAttemptDetail(Number(btn.dataset.attemptIndex)));
}

function renderAttemptDetail(index) {
  const history = mockHistory();
  const attempt = history[index];
  if (!attempt) return renderHistory();
  const subjectRows = Array.isArray(attempt.topics) ? attempt.topics.map(t => `<div class="topic-row"><div><strong>${escapeHtml(t.category)}</strong><div class="small">${t.correct}/${t.total} correct</div></div><div class="topic-bar"><span style="width:${t.percent}%"></span></div><strong>${t.percent}%</strong></div>`).join('') : '<p class="small">Topic detail was not stored by the earlier version of the app.</p>';
  const review = renderStoredReview(attempt);

  app.innerHTML = `<div class="app-shell">${appHeader('history')}
    <main class="dashboard-main">
      <button class="text-back" id="backHistory">← Back to history</button>
      <div class="results-grid stored-result-grid">
        <section class="card result-hero compact-result"><div class="result-kicker">${formatDate(attempt.finishedAt)}</div><div class="score-ring" style="--pct:${attempt.percent}"><div class="score-content"><div class="score-big">${attempt.percent}%</div><div class="small">${attempt.score}/${attempt.total}</div></div></div><h1 class="${attempt.passed ? 'pass' : 'fail'}">${attempt.passed ? 'PASS' : 'NOT YET'}</h1><div class="small result-meta">${attempt.timeUsed || (attempt.elapsedSeconds ? formatDuration(attempt.elapsedSeconds) : '')}</div></section>
        <section class="card result-topics"><h2>Performance by topic</h2>${subjectRows}</section>
        <section class="card answer-review"><div class="review-heading"><h2>Answer review</h2>${attempt.questionResults ? '<button class="btn btn-secondary" id="storedWrongOnly">Show incorrect only</button>' : ''}</div><div id="storedReviewList">${review}</div></section>
      </div>
      ${footerNote()}
    </main>${bottomNav('history')}
  </div>`;
  bindNavigation();
  document.getElementById('backHistory').onclick = renderHistory;
  let wrongOnly = false;
  const toggle = document.getElementById('storedWrongOnly');
  if (toggle) toggle.onclick = () => {
    wrongOnly = !wrongOnly;
    toggle.textContent = wrongOnly ? 'Show all' : 'Show incorrect only';
    document.getElementById('storedReviewList').innerHTML = renderStoredReview(attempt, wrongOnly);
  };
}

function renderStoredReview(attempt, wrongOnly = false) {
  if (!Array.isArray(attempt.questionResults)) return '<div class="empty-state compact"><strong>Detailed review unavailable for this legacy attempt.</strong><span>The previous app version stored only the final score. New attempts will preserve topic and question-level review data locally.</span></div>';
  const items = attempt.questionResults.filter(r => !wrongOnly || !r.wasCorrect);
  if (!items.length) return '<p class="small">No incorrect answers — excellent work.</p>';
  return items.map((r, idx) => {
    const source = findBankQuestion(r.id);
    if (!source) return '';
    return `<article class="review-item"><div class="q-meta">${escapeHtml(r.category)} · ${escapeHtml(r.subtopic)} ${difficultyBadge(source)}</div>${sourceMarkup(source, true)}<div class="review-question">${escapeHtml(source.question)}</div><span class="answer-tag ${r.wasCorrect ? 'correct' : 'wrong'}">Your answer: ${escapeHtml(r.selected || 'Unanswered')}</span>${r.wasCorrect ? '' : `<span class="answer-tag correct">Correct: ${escapeHtml(r.correct)}</span>`}<div class="review-explanation">${escapeHtml(source.explanation)}</div><div class="reference">Indian-law / concept reference: ${escapeHtml(source.reference)}</div></article>`;
  }).join('');
}

function renderPractice() {
  stopTimer();
  currentView = 'practice';
  const history = mockHistory();
  const weak = weakestCategory(history);
  const misses = aggregateMistakes(history).slice(0, 6);
  const subjects = aggregateSubjects(history).sort((a, b) => a.percent - b.percent);

  app.innerHTML = `<div class="app-shell dashboard-shell">${appHeader('practice')}
    <main class="dashboard-main">
      <section class="page-heading"><div><div class="eyebrow">Focused revision</div><h1>Practice your weak areas</h1><p>These untimed ${EXAM_CONFIG.practiceCount}-question sets do not affect your exam-readiness score.</p></div><button class="btn btn-primary" id="startPractice">${icon('target', 19)} Start ${EXAM_CONFIG.practiceCount}-question practice</button></section>
      <div class="practice-layout">
        <section class="card"><div class="card-heading"><h2>Priority subject</h2></div>${weak ? `<div class="priority-big"><span class="subject-icon ${subjectClass(weak)}">${subjectIcon(weak)}</span><div><strong>${escapeHtml(weak)}</strong><span>Questions will be weighted toward this subject.</span></div></div>` : '<div class="empty-state compact"><strong>No weakness data yet.</strong><span>Your first practice set will be mixed across all four subjects.</span></div>'}</section>
        <section class="card"><div class="card-heading"><h2>Subject snapshot</h2></div>${subjects.length ? renderSubjectRows(history) : '<div class="empty-state compact"><strong>Complete a mock first.</strong><span>Subject-level analytics begin after your first full mock.</span></div>'}</section>
        <section class="card practice-misses"><div class="card-heading"><h2>Frequently missed topics</h2></div>${misses.length ? misses.map((m, i) => `<div class="miss-row"><span>${i + 1}</span><div><strong>${escapeHtml(m.subtopic)}</strong><small>${escapeHtml(m.category)}</small></div><b>${m.misses} miss${m.misses === 1 ? '' : 'es'}</b></div>`).join('') : '<div class="empty-state compact"><strong>No stored mistakes yet.</strong><span>Once you complete mocks, your most frequently missed topics will appear here.</span></div>'}</section>
      </div>
      ${footerNote()}
    </main>${bottomNav('practice')}
  </div>`;
  bindNavigation();
  document.getElementById('startPractice').onclick = () => readActive() ? confirmReplaceExam('practice') : startBankAction('practice');
}

function renderSettings() {
  stopTimer();
  currentView = 'settings';
  const history = mockHistory();
  const difficultyCounts = ['S','M','H'].map(level => ({ level, count: QUESTION_BANK.filter(q => q.difficulty === level).length }));
  const sourceCards = Object.entries(SOURCE_CATALOG || {}).map(([id, source]) => `<article class="source-card">
    <div><strong>${escapeHtml(source.shortTitle || source.title)}</strong><span class="license-pill">${escapeHtml(source.license)}</span></div>
    <p>${escapeHtml(source.provenance || '')}</p>
    ${source.url ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>` : '<span class="source-local">Bundled project supplement</span>'}
  </article>`).join('');
  app.innerHTML = `<div class="app-shell dashboard-shell">${appHeader('settings')}
    <main class="dashboard-main settings-main">
      <section class="page-heading"><div><div class="eyebrow">Local preferences & provenance</div><h1>Settings</h1><p>The app has no account or backend. Your progress stays in this browser.</p></div></section>
      <div class="settings-grid">
        <section class="card"><h2>Exam configuration</h2><div class="setting-row"><span>Questions per mock</span><strong>${EXAM_CONFIG.questionCount}</strong></div><div class="setting-row"><span>Time limit</span><strong>${EXAM_CONFIG.durationMinutes} minutes</strong></div><div class="setting-row"><span>Pass threshold</span><strong>${EXAM_CONFIG.passPercent}%</strong></div><div class="setting-row"><span>Unique active questions</span><strong>${originCounts().total}</strong></div><div class="setting-row"><span>Direct source rows</span><strong>${Number(window.OPEN_BANK_STATUS?.directRelevantSourceRows || originCounts().total)}</strong></div><div class="setting-row"><span>Duplicate stems removed</span><strong>${Number(window.OPEN_BANK_STATUS?.duplicateDirectStemsRemoved || 0)}</strong></div><div class="setting-row"><span>AI-authored questions active</span><strong>0</strong></div><div class="setting-row"><span>Mock category mix</span><strong>30 Companies · 10 Securities · 6 Accountancy · 4 Governance</strong></div></section>
        <section class="card"><h2>Difficulty legend</h2><div class="difficulty-legend"><div>${difficultyBadge({difficulty:'S'})}<span><strong>Simple</strong><small>Direct recall / core rule</small></span><b>${difficultyCounts.find(x=>x.level==='S').count}</b></div><div>${difficultyBadge({difficulty:'M'})}<span><strong>Medium</strong><small>Application / board context</small></span><b>${difficultyCounts.find(x=>x.level==='M').count}</b></div><div>${difficultyBadge({difficulty:'H'})}<span><strong>Hard</strong><small>Judgement / scenario challenge</small></span><b>${difficultyCounts.find(x=>x.level==='H').count}</b></div></div></section>
        <section class="card"><h2>Readiness score</h2><p class="settings-copy">The training-readiness number is deliberately not a pass probability. After three mocks it uses 70% of your last-three average and 30% of your overall average. Before three mocks, it shows your current average.</p></section>
        <section class="card"><h2>Local data</h2><p class="settings-copy">${history.length} completed mock${history.length === 1 ? '' : 's'} stored on this device. Clearing data removes history and any unfinished session.</p><button class="btn btn-danger" id="clearData">Clear all local data</button></section>
        <section class="card source-catalog-card"><h2>Question-bank sources</h2><p class="settings-copy">This build contains only the 133 source rows classified as directly relevant to the IICA Independent Director assessment. Two duplicate stems are collapsed, leaving 131 unique active questions. The 68 supplementary and 6,428 excluded questions are not shipped. No AI-authored questions are used. Items flagged for current-law or source-answer validation remain visibly marked in review details.</p><div class="bank-sync-actions"><button class="btn btn-secondary" id="refreshOpenBank">Recheck bundled question bank</button><small>${escapeHtml((window.OPEN_BANK_STATUS?.lastSync && `Build: ${new Date(window.OPEN_BANK_STATUS.lastSync).toLocaleString()}`) || 'Bundled static bank')}</small></div><div class="source-catalog">${sourceCards}</div></section>
        <section class="card"><h2>Legal content</h2><p class="settings-copy">Legal-content review date: <strong>${escapeHtml(EXAM_CONFIG.legalReviewDate)}</strong>. SEBI/MCA/IICA materials are used as validation/reference sources where appropriate, not copied as question-bank content. This app is unofficial and regulations may change.</p></section>
      </div>
      ${footerNote()}
    </main>${bottomNav('settings')}
  </div>`;
  bindNavigation();
  const refreshOpenBank = document.getElementById('refreshOpenBank');
  if (refreshOpenBank) refreshOpenBank.onclick = async () => {
    refreshOpenBank.disabled = true;
    refreshOpenBank.textContent = 'Refreshing…';
    try { await window.syncOpenBank?.(); } finally { renderSettings(); }
  };
  document.getElementById('clearData').onclick = () => showModal('Clear all local data?', 'This permanently removes mock history and any unfinished session from this browser.', [
    { label: 'Cancel', cls: 'btn-secondary', action: closeModal },
    { label: 'Clear data', cls: 'btn-danger', action: () => { Object.values(STORAGE).forEach(key => localStorage.removeItem(key)); closeModal(); renderSettings(); } }
  ]);
}

function startTimer() {
  stopTimer();
  const tick = () => {
    if (!state || state.status !== 'active' || state.kind !== 'mock') return;
    const seconds = Math.ceil((state.deadline - Date.now()) / 1000);
    if (seconds <= 0) { submitExam(true); return; }
    const el = document.getElementById('timer');
    if (el) { el.textContent = formatTime(seconds); el.classList.toggle('danger', seconds <= 300); }
  };
  tick();
  timerId = setInterval(tick, 1000);
}

function stopTimer() { if (timerId) { clearInterval(timerId); timerId = null; } }

function showModal(title, body, buttons) {
  closeModal();
  const wrap = document.createElement('div');
  wrap.className = 'modal-backdrop';
  wrap.id = 'modal';
  wrap.innerHTML = `<div class="modal" role="dialog" aria-modal="true"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p><div class="actions" id="modalActions"></div></div>`;
  document.body.appendChild(wrap);
  const actions = wrap.querySelector('#modalActions');
  buttons.forEach(b => {
    const el = document.createElement('button');
    el.className = `btn ${b.cls}`;
    el.textContent = b.label;
    el.onclick = b.action;
    actions.appendChild(el);
  });
}

function closeModal() { document.getElementById('modal')?.remove(); }

window.addEventListener('beforeunload', saveActive);
if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}));

renderHome();
window.addEventListener('openbank-updated', () => { if (currentView === 'home' || currentView === 'settings') navigate(currentView); });
