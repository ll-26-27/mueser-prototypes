/* The reading room renders itself from the JSON blob in #reading-data. Nothing here changes the build; every
   action becomes an event in localStorage and, when served, in outputs/reading/log.jsonl via POST /api/log. */
(() => {
  'use strict';
  const DATA = JSON.parse(document.getElementById('reading-data').textContent);
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const uniq = a => [...new Set(a)];
  const short = m => (m || '').split(':').pop().split('/').pop();
  const KEY = 'mueser.reading.' + (DATA.case || 'case');
  const PREF = KEY + '.prefs';
  const app = $('#rr-app');

  // ---------- time, ids ----------
  const pad = n => String(n).padStart(2, '0');
  const stamp = () => {
    const d = new Date(), off = -d.getTimezoneOffset(), sign = off >= 0 ? '+' : '-', a = Math.abs(off);
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${sign}${pad(Math.floor(a / 60))}${pad(a % 60)}`;
  };
  const uuid = () => (crypto.randomUUID ? crypto.randomUUID().replace(/-/g, '') : Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join(''));

  // ---------- store ----------
  const store = {
    local: [], synced: new Set(), connected: false, serverBuild: null,
    load() {
      try { const s = JSON.parse(localStorage.getItem(KEY) || '{}'); this.local = s.events || []; this.synced = new Set(s.synced || []); } catch (_) { this.local = []; this.synced = new Set(); }
    },
    persist() { try { localStorage.setItem(KEY, JSON.stringify({ events: this.local, synced: [...this.synced] })); } catch (_) { /* private window or blocked storage: the page still works */ } },
    all() {
      const seen = new Set(), out = [];
      for (const e of [...(DATA.log || []), ...this.local]) { if (!seen.has(e.id)) { seen.add(e.id); out.push(e); } }
      return out.sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0));
    },
    async ping() {
      if (!/^https?:$/.test(location.protocol)) return;
      try {
        const r = await fetch('/api/ping', { cache: 'no-store' });
        if (!r.ok) return;
        const j = await r.json(); this.connected = true; this.serverBuild = j.build_id || null;
        if (j.who && !prefs.who) { prefs.who = j.who; savePrefs(); }
        // push anything written while the server was away
        for (const e of this.local) if (!this.synced.has(e.id)) await this.post(e);
      } catch (_) { this.connected = false; }
    },
    async post(e) {
      try {
        const r = await fetch('/api/log', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(e) });
        if (r.ok) { this.synced.add(e.id); this.persist(); return true; }
        const t = await r.text(); toast('Not saved: ' + t.slice(0, 160)); return false;
      } catch (_) { this.connected = false; renderBar(); return false; }
    },
    async add(e) {
      this.local.push(e); this.persist();
      if (this.connected) await this.post(e);
      renderWork(); renderBar();
    },
    exportAll() {
      const lines = this.local.map(e => JSON.stringify(e)).join('\n') + (this.local.length ? '\n' : '');
      const blob = new Blob([lines], { type: 'application/x-ndjson' });
      const a = el('a'); a.href = URL.createObjectURL(blob);
      a.download = `${(prefs.who || 'reader').replace(/[^\w-]+/g, '_')}-${stamp().replace(/[:+]/g, '').replace('T', '-')}.jsonl`;
      document.body.append(a); a.click(); a.remove();
      toast(`Exported ${this.local.length} event${this.local.length === 1 ? '' : 's'}. Drop the file into ${DATA.paths.inbox} and run: python -m mueser.reading ingest --case ${DATA.case}`);
    },
  };
  let prefs = { who: '', mode: null, marks: 'review', page: null, log: { scope: 'page', type: 'all', status: 'open' }, showLog: true };
  try { prefs = { ...prefs, ...JSON.parse(localStorage.getItem(PREF) || '{}') }; } catch (_) { /* defaults */ }
  const savePrefs = () => { try { localStorage.setItem(PREF, JSON.stringify(prefs)); } catch (_) { /* fine */ } };

  const mk = (type, anchor, body, ref) => ({ id: 'evt_' + uuid(), ts: stamp(), who: prefs.who || '', client: DATA.client, build_id: DATA.build_id, type, anchor: anchor || null, body: body || {}, ref: ref || null });
  const decisions = () => { const m = {}; for (const e of store.all()) if (e.type === 'decision' && e.body && e.body.target) m[e.body.target] = e; return m; };
  const statuses = () => { const s = {}; for (const e of store.all()) if (['issue', 'question', 'comment'].includes(e.type)) s[e.id] = 'open'; for (const e of store.all()) if (e.type === 'status' && e.body && e.body.target in s) s[e.body.target] = e.body.status || 'open'; return s; };

  // ---------- state ----------
  const pages = DATA.pages;
  let pageIdx = Math.max(0, pages.findIndex(p => p.page_id === (decodeURIComponent(location.hash.slice(1)) || prefs.page)));
  const page = () => pages[pageIdx];
  const hasTranslation = pg => !!(pg.translation && pg.translation.blocks && pg.translation.blocks.length);
  const mode = () => prefs.mode || (hasTranslation(page()) ? 'both' : 'transcription');
  const docOf = pg => ((DATA.metadata || {}).docs || {})[pg.doc_id] || { title: pg.doc_id, pages: {} };
  const pageLabel = pg => ((docOf(pg).pages || {})[pg.page_id] || {}).label || pg.page_id;

  // ---------- helpers for text and citations ----------
  const splitName = n => { n = n.trim(); if (n.includes(',')) { const [f, g] = n.split(',', 2); return { family: f.trim(), given: g.trim() }; } const p = n.split(/\s+/); return p.length === 1 ? { family: p[0] } : { family: p[p.length - 1], given: p.slice(0, -1).join(' ') }; };
  const authorsShort = doc => { const f = (doc.author || []).map(a => splitName(a).family); if (!f.length) return doc.archive || ''; if (f.length === 1) return f[0]; if (f.length === 2) return `${f[0]} and ${f[1]}`; return `${f[0]} et al.`; };
  const lineLabel = ids => { const n = ids.map(x => +x.slice(1)).filter(Number.isFinite).sort((a, b) => a - b); if (!n.length) return ''; return n.length === 1 ? `l. ${n[0]}` : `ll. ${n[0]}–${n[n.length - 1]}`; };
  function citeFor(pg, lineIds, layer, quote, block) {
    const doc = docOf(pg), label = pageLabel(pg), lines = lineLabel(lineIds), dec = decisions();
    const where = [label, lines].filter(Boolean).join(', ');
    const imprint = [doc.place, doc.date].filter(Boolean).join(', ');
    let head = authorsShort(doc) ? `${authorsShort(doc)}, ${doc.title || pg.doc_id}` : (doc.title || pg.doc_id);
    if (imprint) head += ` (${imprint})`;
    const arch = [doc.archive, doc.shelfmark].filter(Boolean).join(', ');
    let plain = `${head}, ${where}.`;
    if (arch && ['manuscript', 'personal_communication', 'letter'].includes(doc.type)) plain = `${head}, ${where}. ${arch}.`;
    if (doc.synthetic) plain += ' Synthetic page: invented text rendered for testing, not a historical source.';
    if (layer === 'translation') plain += ' English translation.';
    const nDec = lineIds.reduce((n, lid) => { const l = pg.lines.find(x => x.line_id === lid); if (!l) return n; if (dec[`line:${pg.page_id}:${lid}`]) n++; for (const sp of l.spans) if (sp.piece === 0 && dec[`span:${pg.page_id}:${sp.span_id}`]) n++; return n; }, 0);
    const whoDec = uniq(lineIds.flatMap(lid => { const l = pg.lines.find(x => x.line_id === lid); return l ? l.spans.map(sp => (dec[`span:${pg.page_id}:${sp.span_id}`] || {}).who).filter(Boolean) : []; }));
    let prov = `Transcription: medoid ${pg.diplomatic.reader}, run ${pg.diplomatic.run_id}, settled build ${DATA.build_id}` + (nDec ? `, ${nDec} decision${nDec === 1 ? '' : 's'}${whoDec.length ? ' by ' + whoDec.join(', ') : ''}` : '') + '.';
    if (layer === 'translation' && pg.translation) {
      const b = block || null, d = b ? dec[`block:${pg.page_id}:${b.block_id}`] : null;
      const model = d && d.body.choice === 'b' ? pg.translation.models[1] : d && d.body.choice === 'custom' ? 'a person' : pg.translation.models[0];
      prov += ` Translation: ${model}, run ${pg.translation.run_id}` + (b ? `, block ${b.block_id}` + (d ? ` decided by ${d.who || 'a reader'}` : '') : '') + '.';
    }
    plain += ' ' + prov;
    const repo = `${DATA.case}/outputs/reading/builds/${DATA.build_id}/settled.json · ${pg.page_id} ${lineIds.join(' ')}`;
    const markdown = (quote ? '> ' + quote.replace(/\n/g, '\n> ') + '\n\n' : '') + `[^1]: ${plain} \`${repo}\``;
    const csl = { type: doc.type || 'document', title: doc.title || pg.doc_id };
    if (doc.author) csl.author = doc.author.map(splitName);
    const y = String(doc.date || '').match(/\d{4}/); if (y) csl.issued = { 'date-parts': [[+y[0]]] };
    for (const [s, d] of [['publisher', 'publisher'], ['place', 'publisher-place'], ['url', 'URL'], ['archive', 'archive'], ['shelfmark', 'archive_location'], ['language', 'language']]) if (doc[s]) csl[d] = doc[s];
    csl.locator = label.replace(/^(p\.|pp\.|S\.|fol\.)\s*/, '') + (lines ? `, ${lines}` : ''); csl.label = 'page';
    csl.note = ((doc.synthetic ? 'Synthetic page, not a historical source. ' : '') + (layer === 'translation' ? 'English translation. ' : '') + prov).trim();
    return { plain, markdown, csl, csl_json: JSON.stringify(csl, null, 1) };
  }
  function wordDiff(a, b) {
    const A = a.split(/(\s+)/), B = b.split(/(\s+)/);
    const n = A.length, m = B.length, L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    const outA = [], outB = []; let i = 0, j = 0;
    while (i < n && j < m) {
      if (A[i] === B[j]) { outA.push([A[i], false]); outB.push([B[j], false]); i++; j++; }
      else if (L[i + 1][j] >= L[i][j + 1]) { outA.push([A[i], true]); i++; }
      else { outB.push([B[j], true]); j++; }
    }
    while (i < n) outA.push([A[i++], true]); while (j < m) outB.push([B[j++], true]);
    return [outA, outB];
  }
  const diffNode = parts => { const f = document.createDocumentFragment(); for (const [t, changed] of parts) { if (changed && t.trim()) { const m = el('span', 'dmark', t); f.append(m); } else f.append(document.createTextNode(t)); } return f; };
  function offsetWithin(container, node, offset) {
    // character offset of (node, offset) inside container's visible text, skipping nothing: lids are CSS, buttons live outside .ln
    let n = 0; const w = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    if (node.nodeType !== 3) { // element boundary: count text before child[offset]
      const target = node.childNodes[offset] || null; let cur;
      while ((cur = w.nextNode())) { if (target && (cur === target || target.contains(cur))) break; if (target && target.compareDocumentPosition(cur) & Node.DOCUMENT_POSITION_FOLLOWING) break; n += cur.length; }
      return n;
    }
    let cur; while ((cur = w.nextNode())) { if (cur === node) return n + offset; n += cur.length; }
    return n;
  }

  // ---------- rendering ----------
  let barEl, noticeEl, workEl, footEl;
  function renderAll() {
    app.replaceChildren();
    barEl = el('div', 'rr-bar'); noticeEl = el('div'); workEl = el('div', 'rr-work'); footEl = el('div', 'rr-foot');
    app.append(barEl, noticeEl, workEl, footEl);
    renderBar(); renderWork(); renderFoot();
  }
  function renderBar() {
    if (!barEl) return;
    barEl.replaceChildren();
    const pg = page();
    const pager = el('div', 'rr-pager');
    const head = el('div', 'rr-pager-head');
    head.append(el('span', 'eyebrow', `Source page ${pageIdx + 1} of ${pages.length}`));
    const prev = el('button', 'ghost', '← Previous'), next = el('button', 'ghost', 'Next →');
    prev.disabled = pageIdx === 0; next.disabled = pageIdx === pages.length - 1;
    prev.title = 'Previous page (← key)'; next.title = 'Next page (→ key)';
    prev.onclick = () => goPage(pageIdx - 1); next.onclick = () => goPage(pageIdx + 1);
    const add = el('button', 'ghost', '+ Add a source'); add.title = 'How to bring another document into this room';
    add.onclick = () => openAddSource(add);
    head.append(prev, next, add);
    const nav = el('div', 'rr-pages'); nav.setAttribute('role', 'tablist'); nav.setAttribute('aria-label', 'Pages in this reading room');
    pages.forEach((p, i) => {
      const b = el('button'); b.setAttribute('role', 'tab'); b.setAttribute('aria-current', String(i === pageIdx));
      b.append(el('small', 'n', `${i + 1}`), document.createTextNode(docOf(p).title || p.doc_id), el('small', '', `${pageLabel(p)} · ${(docOf(p).date || '')}${docOf(p).synthetic ? ' · synthetic' : ''}`));
      b.onclick = () => goPage(i);
      nav.append(b);
    });
    pager.append(head, nav);
    const modeBox = el('div', 'rr-mode'); modeBox.setAttribute('role', 'group'); modeBox.setAttribute('aria-label', 'What to show beside the scan');
    for (const [v, label] of [['transcription', 'Transcription'], ['translation', 'Translation'], ['both', 'Both']]) {
      const b = el('button', '', label); b.setAttribute('aria-pressed', String(mode() === v));
      if (v !== 'transcription' && !hasTranslation(pg)) { b.disabled = true; b.title = 'No translation run for this page yet'; }
      b.onclick = () => { prefs.mode = v; savePrefs(); renderBar(); renderWork(); };
      modeBox.append(b);
    }
    const who = el('label', 'rr-who'); who.append('Reading as'); const inp = el('input'); inp.value = prefs.who || ''; inp.placeholder = 'your name'; inp.setAttribute('aria-label', 'Your name, written on every event');
    inp.onchange = () => { prefs.who = inp.value.trim(); savePrefs(); }; who.append(inp);
    const conn = el('span', 'rr-conn' + (store.connected ? '' : ' off'), store.connected ? `Saving to ${DATA.paths.log}` : 'Not connected · kept in this browser');
    conn.title = store.connected ? 'Every event is appended to the log on disk as you make it.' : 'Open the page through `python -m mueser.reading serve` to write straight into the log, or use Export.';
    const exp = el('button', 'ghost', 'Export log ↓'); exp.onclick = () => store.exportAll(); exp.title = 'Download every event made in this browser as JSONL';
    const logBtn = el('button', 'ghost', prefs.showLog ? 'Hide log' : 'Show log'); logBtn.onclick = () => { prefs.showLog = !prefs.showLog; savePrefs(); renderBar(); renderWork(); };
    barEl.append(pager, el('span', 'grow'), modeBox, who, conn, exp, logBtn);
    // notices
    noticeEl.replaceChildren();
    const dec = decisions();
    const pending = Object.values(dec).filter(e => { const [kind, pid, id] = e.body.target.split(':'); const p = pages.find(x => x.page_id === pid); if (!p) return false; if (kind === 'span') { const sp = p.lines.flatMap(l => l.spans).find(s => s.span_id === id); return sp ? sp.status !== 'decided' : false; } if (kind === 'line') return true; if (kind === 'block') return !(p.translation && p.translation.resolved && p.translation.resolved.some(r => r.block_id === id)); return false; }).length;
    if (pending) { const n = el('p', 'rr-notice'); n.append(`${pending} decision${pending === 1 ? '' : 's'} made since build `, el('code', '', DATA.build_id), '. They show here as decided; to settle them into the text run ', el('code', '', `python -m mueser.reading apply --case ${DATA.case}`), ' then ', el('code', '', 'build'), '.'); noticeEl.append(n); }
    if (!store.connected && /^https?:$/.test(location.protocol) === false) { const n = el('p', 'rr-notice'); n.append('Opened as a file: your decisions and notes are kept in this browser only. ', el('b', '', 'Export log'), ' writes them to a file; drop it into ', el('code', '', DATA.paths.inbox), ' and run ', el('code', '', `python -m mueser.reading ingest --case ${DATA.case}`), '. Or open the page with ', el('code', '', `python -m mueser.reading serve --case ${DATA.case}`), ' and it saves as you go.'); noticeEl.append(n); }
    if (store.connected && store.serverBuild && store.serverBuild !== DATA.build_id) { const n = el('p', 'rr-notice'); n.append(`The server has a newer build (${store.serverBuild}) than this page (${DATA.build_id}). Reload after running build.`); noticeEl.append(n); }
    if (pg.consensus && pg.consensus.agreement < 0.6) { const n = el('p', 'rr-notice'); n.append(`Readers disagreed too much on this page for span-by-span decisions (agreement ${pg.consensus.agreement.toFixed(2)}). Read the text against the image and use ✎ at the end of a line to replace the whole line.`); noticeEl.append(n); }
  }

  function rowsFor(pg) {
    const lines = pg.lines;
    if (!hasTranslation(pg)) return lines.map(l => ({ lines: [l], blocks: [] }));
    const byLine = new Map();
    for (const b of pg.translation.blocks) for (const lid of b.lines) if (!byLine.has(lid)) byLine.set(lid, b);
    const rows = []; let i = 0;
    while (i < lines.length) {
      const b = byLine.get(lines[i].line_id);
      if (!b) { rows.push({ lines: [lines[i]], blocks: [] }); i++; continue; }
      const grp = []; while (i < lines.length && byLine.get(lines[i].line_id) === b) grp.push(lines[i++]);
      rows.push({ lines: grp, blocks: [b] });
    }
    const placed = new Set(rows.flatMap(r => r.blocks.map(b => b.block_id)));
    for (const b of pg.translation.blocks) if (!placed.has(b.block_id)) { const r = rows.find(r => r.lines.some(l => b.lines.includes(l.line_id))) || rows[rows.length - 1]; r.blocks.push(b); }
    return rows;
  }

  function renderWork() {
    if (!workEl) return;
    closePop(); hideFloat();
    const pg = page(); const dec = decisions();
    workEl.replaceChildren(); workEl.className = 'rr-work' + (prefs.showLog ? ' with-log' : '');
    // image
    const imgBox = el('div', 'rr-image');
    const lab = el('div', 'image-label'); lab.append(el('span', '', 'Original document'), el('span', 'mono', pg.page_id)); imgBox.append(lab);
    const fig = el('div', 'fig show-boxes'); const img = el('img'); img.src = pg.image; img.alt = `${docOf(pg).title || pg.doc_id}, ${pageLabel(pg)}`; img.loading = 'eager';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', `0 0 ${pg.width} ${pg.height}`); svg.setAttribute('preserveAspectRatio', 'none');
    for (const l of pg.lines) {
      const a = l.anchor; if (!a || !a.bbox) continue;
      const r = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      const [x, y, w, h] = a.bbox; r.setAttribute('x', x); r.setAttribute('y', y); r.setAttribute('width', w); r.setAttribute('height', h); r.dataset.line = l.line_id;
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'title'); t.textContent = `${l.line_id} · ${a.op}${a.confidence != null ? ` · confidence ${a.confidence}` : ''}\n${l.settled}`; r.append(t);
      r.addEventListener('mouseenter', () => hot([l.line_id])); r.addEventListener('mouseleave', () => hot([]));
      r.addEventListener('click', () => goTo(pg.page_id, [l.line_id]));
      svg.append(r);
    }
    fig.append(img, svg); imgBox.append(fig);
    const tools = el('div', 'tools'); const cb = el('label'); const ck = el('input'); ck.type = 'checkbox'; ck.checked = true; ck.onchange = () => fig.classList.toggle('show-boxes', ck.checked); cb.append(ck, ' Show line boxes'); tools.append(cb);
    const open = el('a', '', 'Open image ↗'); open.href = pg.image; open.target = '_blank'; tools.append(open); imgBox.append(tools);
    if (pg.anchors) { const a = pg.anchors; imgBox.append(el('div', 'anchors', `Lines anchored to ${short(a.segmentation && a.segmentation.reader)} boxes: ${a.matched} matched · ${a.merged} merged · ${a.split} split · ${a.unanchored} unanchored${a.dropped_polygons ? ` · ${a.dropped_polygons} polygon${a.dropped_polygons === 1 ? '' : 's'} with no text` : ''}${a.mean_confidence != null ? ` · mean confidence ${a.mean_confidence}` : ''}`)); }
    else imgBox.append(el('div', 'anchors', 'No segmentation with boxes for this page: selections cannot be shown on the scan.'));
    // text
    const txt = el('div', 'rr-text mode-' + mode());
    const head = el('div', 'head');
    head.append(el('span', '', `Transcription: medoid of ${pg.consensus.readers.length} readers, `), el('b', '', short(pg.diplomatic.reader)), el('span', '', ` · agreement ${pg.consensus.agreement.toFixed(3)} · ${pg.consensus.check_in} passage${pg.consensus.check_in === 1 ? '' : 's'} to check`));
    if (hasTranslation(pg)) { const tr = pg.translation; head.append(el('span', '', `Translation: ${tr.models.map(short).join(' · ')} · ${tr.blocks.filter(b => b.divergent).length} of ${tr.blocks.length} blocks diverge${tr.stale ? ' · STALE: the text changed after this translation' : ''}`)); }
    txt.append(head);
    const filters = el('div', 'filters'); const fl = el('label'); fl.append('Highlight '); const fs = el('select');
    for (const [v, t] of [['review', 'passages to check'], ['all', 'every disagreement'], ['none', 'nothing']]) { const o = el('option', '', t); o.value = v; fs.append(o); }
    fs.value = prefs.marks || 'review'; fs.onchange = () => { prefs.marks = fs.value; savePrefs(); rows.className = 'rows' + (fs.value === 'review' ? ' hide-weak' : fs.value === 'none' ? ' hide-marks' : ''); }; fl.append(fs); filters.append(fl);
    filters.append(el('span', 'muted', 'Select text to see it on the scan, copy it with a citation, or leave a note. Click a highlighted passage to decide it. ✎ at a line’s end replaces the whole line.'));
    txt.append(filters);
    const rows = el('div', 'rows' + (prefs.marks === 'review' || !prefs.marks ? ' hide-weak' : prefs.marks === 'none' ? ' hide-marks' : ''));
    for (const row of rowsFor(pg)) {
      const r = el('div', 'row'); const cs = el('div', 'col-src'), ct = el('div', 'col-tr');
      for (const l of row.lines) cs.append(renderLine(pg, l, dec));
      for (const b of row.blocks) ct.append(renderBlock(pg, b, dec));
      if (hasTranslation(pg) && !row.blocks.length) { const e = el('div', 'seg empty', row.lines.every(l => !l.settled.trim()) ? '' : 'no segment covers this line'); e.dataset.lines = row.lines.map(l => l.line_id).join(' '); ct.append(e); }
      r.append(cs, ct); rows.append(r);
    }
    txt.append(rows);
    workEl.append(imgBox, txt);
    if (prefs.showLog) workEl.append(renderLog());
  }

  function decidedText(sp, d, orig) {
    const c = d.body.choice || 'keep';
    if (c === 'keep') return orig;
    if (sp.piece > 0) return '';
    if (c === 'alt') { const t = sp.alternatives[d.body.reader]; return t != null ? t : (d.body.text || ''); }
    return d.body.text || '';
  }
  function renderLine(pg, l, dec) {
    const wrap = el('div', 'lnwrap');
    const s = el('span', 'ln'); s.dataset.line = l.line_id;
    if (!l.anchor || l.anchor.op === 'unanchored') { s.classList.add('unanchored'); s.title = 'No box on the scan for this line'; }
    const ld = dec[`line:${pg.page_id}:${l.line_id}`];
    if (ld) { s.classList.add('decided-line'); s.textContent = ld.body.text || ''; s.title = `Whole line decided by ${ld.who || 'a reader'} on ${ld.ts}. Was: ${l.settled}`; }
    else {
      let pos = 0; const text = l.settled; const minw = pg.consensus.min_weight || 0.25;
      for (const sp of l.spans) {
        if (sp.start > pos) s.append(document.createTextNode(text.slice(pos, sp.start)));
        const m = el('mark'); m.dataset.span = sp.span_id; m.dataset.piece = sp.piece; m.tabIndex = 0; m.setAttribute('role', 'button');
        if ((sp.weight || 0) >= minw) m.classList.add('strong');
        const orig = text.slice(sp.start, sp.end);
        const d = dec[`span:${pg.page_id}:${sp.span_id}`];
        if (d) { m.classList.add('decided'); m.textContent = decidedText(sp, d, orig); m.title = `Decided by ${d.who || 'a reader'} (${d.body.choice}${d.body.reader ? ', ' + short(d.body.reader) : ''}) on ${d.ts}. Medoid had: “${orig}”${d.body.note ? '\nNote: ' + d.body.note : ''}`; }
        else {
          if (sp.start === sp.end) { m.classList.add('ins'); m.textContent = '‸'; } else m.textContent = orig;
          const alts = Object.entries(sp.alternatives).map(([k, v]) => `${short(k)}: ${v ? '“' + v + '”' : '(nothing)'}`).join('\n');
          m.title = `${Object.keys(sp.alternatives).length} of ${pg.consensus.readers.length - 1} readers differ (weight ${(sp.weight || 0).toFixed(2)})${sp.of > 1 ? ` · part ${sp.piece + 1} of ${sp.of} of a span across lines` : ''}\n${alts}\nClick to decide.`;
        }
        m.setAttribute('aria-label', m.title.split('\n')[0]);
        const openIt = () => openSpanDecision(pg, l, sp, m);
        m.onclick = e => { e.preventDefault(); e.stopPropagation(); openIt(); };
        m.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openIt(); } };
        s.append(m); pos = Math.max(pos, sp.end);
      }
      if (pos < text.length) s.append(document.createTextNode(text.slice(pos)));
      if (!text.length) s.append(document.createTextNode(' '));
    }
    s.addEventListener('mouseenter', () => hot([l.line_id])); s.addEventListener('mouseleave', () => hot([]));
    const edit = el('button', 'edit', '✎'); edit.title = 'Replace this whole line'; edit.setAttribute('aria-label', `Replace line ${l.line_id}`);
    edit.onclick = e => { e.stopPropagation(); openLineDecision(pg, l, edit); };
    wrap.append(s, edit);
    return wrap;
  }
  function renderBlock(pg, b, dec) {
    const seg = el('div', 'seg'); seg.dataset.lines = b.lines.join(' '); seg.dataset.block = b.block_id;
    const [ma, mb] = pg.translation.models; const d = dec[`block:${pg.page_id}:${b.block_id}`];
    const notes = (pg.translation.segments || {});
    const segNotes = [];
    for (const m of [ma, mb]) for (const sid of ((m === ma ? b.a : b.b) || {}).segments || []) { const sg = (notes[m] || []).find(x => x.segment_id === sid); if (sg && sg.note) segNotes.push(`${short(m)}: ${sg.note}`); if (sg && sg.verified === false) segNotes.push(`${short(m)}: line reference could not be verified`); }
    if (d) {
      seg.classList.add('decided');
      const c = d.body.choice || 'a'; const text = c === 'b' ? (b.b || {}).text : c === 'custom' ? d.body.text : (b.a || {}).text;
      seg.append(el('span', 'tag', c === 'custom' ? `${d.who || 'reader'}` : short(c === 'b' ? mb : ma)), document.createTextNode(text || ''));
      const ch = el('button', 'decide', 'Change'); ch.onclick = e => { e.stopPropagation(); openBlockDecision(pg, b, ch); }; seg.append(el('span', 'note', `Decided by ${d.who || 'a reader'} on ${d.ts}${d.body.note ? ' · ' + d.body.note : ''}`), ch);
    } else if (b.divergent && b.a && b.b) {
      seg.classList.add('divergent');
      const [pa, pb] = wordDiff(b.a.text, b.b.text);
      const A = el('div'); A.append(el('span', 'tag', short(ma)), diffNode(pa)); const B = el('div', 'alt'); B.append(el('span', 'tag', short(mb)), diffNode(pb));
      seg.append(A, B);
      const btn = el('button', 'decide', 'Decide'); btn.onclick = e => { e.stopPropagation(); openBlockDecision(pg, b, btn); }; seg.append(el('span', 'note', `The two translations differ (distance ${(b.dist || 0).toFixed(2)}).`), btn);
    } else if (b.a) {
      seg.append(el('span', 'tag', short(ma)), document.createTextNode(b.a.text));
      if (b.b) { seg.title = `${short(mb)}: ${b.b.text}`; const alt = el('button', 'decide', 'Other reading'); alt.onclick = e => { e.stopPropagation(); openBlockDecision(pg, b, alt); }; seg.append(alt); }
    } else if (b.b) {
      seg.append(el('span', 'tag', short(mb)), document.createTextNode(b.b.text));
    }
    if (segNotes.length) seg.append(el('span', 'note', segNotes.join(' · ')));
    if (pg.translation.stale) seg.append(el('span', 'note stale', 'The transcription changed after this translation was made.'));
    seg.addEventListener('mouseenter', () => hot(b.lines)); seg.addEventListener('mouseleave', () => hot([]));
    return seg;
  }

  function renderLog() {
    const box = el('aside', 'rr-log'); box.setAttribute('aria-label', 'Log');
    const all = store.all(), st = statuses(), pg = page();
    const open = all.filter(e => ['issue', 'question', 'comment'].includes(e.type) && st[e.id] === 'open').length;
    box.append(el('h2', '', `Log · ${open} open`));
    const f = el('div', 'filters');
    const mkSel = (key, opts) => { const s = el('select'); for (const [v, t] of opts) { const o = el('option', '', t); o.value = v; s.append(o); } s.value = prefs.log[key]; s.onchange = () => { prefs.log[key] = s.value; savePrefs(); renderWork(); }; return s; };
    f.append(mkSel('scope', [['page', 'this page'], ['all', 'all pages']]), mkSel('type', [['all', 'everything'], ['issue', 'issues'], ['question', 'questions'], ['comment', 'comments'], ['decision', 'decisions'], ['excerpt', 'excerpts']]), mkSel('status', [['open', 'open'], ['all', 'open and resolved'], ['resolved', 'resolved']]));
    box.append(f);
    const shown = all.filter(e => e.type !== 'status' && e.type !== 'highlight').filter(e => prefs.log.scope === 'all' || (e.anchor && e.anchor.page === pg.page_id))
      .filter(e => prefs.log.type === 'all' || e.type === prefs.log.type)
      .filter(e => { if (!(e.id in st)) return prefs.log.status !== 'resolved'; return prefs.log.status === 'all' || (prefs.log.status === 'open' ? st[e.id] === 'open' : st[e.id] !== 'open'); })
      .reverse();
    if (!shown.length) box.append(el('p', 'empty', 'Nothing here yet. Select a passage and leave a question, or decide a highlighted passage.'));
    for (const e of shown) {
      const it = el('div', 'item' + (st[e.id] && st[e.id] !== 'open' ? ' resolved' : ''));
      const meta = el('div', 'meta'); meta.append(el('span', 'badge ' + e.type, e.type), el('span', '', e.who || 'unsigned'), el('span', '', e.ts.replace('T', ' ').slice(0, 16)));
      if (e.anchor) meta.append(el('span', 'mono', `${e.anchor.page === pg.page_id ? '' : e.anchor.page + ' '}${(e.anchor.lines || []).join(' ')}${e.anchor.layer === 'translation' ? ' (translation)' : ''}`));
      it.append(meta);
      if (e.anchor && e.anchor.quote) it.append(el('div', 'quote', e.anchor.quote));
      if (e.type === 'decision') it.append(el('div', 'text', `${e.body.target.split(':')[0]} ${e.body.target.split(':').slice(2).join(':')}: ${e.body.choice}${e.body.reader ? ' (' + short(e.body.reader) + ')' : ''}${e.body.text != null && e.body.choice !== 'keep' ? ' → “' + e.body.text + '”' : ''}${e.body.note ? ' · ' + e.body.note : ''}`));
      else if (e.type === 'excerpt') it.append(el('div', 'text', `copied as ${e.body.format}`));
      else if (e.body && e.body.text) it.append(el('div', 'text', e.body.text));
      const acts = el('div', 'acts');
      if (e.anchor && e.anchor.lines && e.anchor.lines.length) { const g = el('button', '', 'Go to'); g.onclick = () => goTo(e.anchor.page, e.anchor.lines); acts.append(g); }
      if (e.id in st) { const r = el('button', '', st[e.id] === 'open' ? 'Resolve' : 'Reopen'); r.onclick = () => store.add(mk('status', e.anchor, { target: e.id, status: st[e.id] === 'open' ? 'resolved' : 'open', note: '' }, e.id)); acts.append(r); }
      if (st[e.id] === 'open') { const rp = el('button', '', 'Reply'); rp.onclick = () => openNote('comment', e.anchor, rp, e.id); acts.append(rp); }
      it.append(acts); box.append(it);
    }
    return box;
  }
  function renderFoot() {
    if (!footEl) return;
    footEl.replaceChildren(); const pg = page();
    const d = el('details'); d.append(el('summary', '', 'Where this page comes from · readers, runs, build'));
    const inner = el('div'); const t = el('table');
    const row = (k, v) => { const tr = el('tr'); tr.append(el('th', '', k), el('td', 'mono', v == null ? '' : String(v))); t.append(tr); };
    row('build', `${DATA.build_id}${DATA.parent_build ? ' (from ' + DATA.parent_build + ')' : ''} · created ${DATA.created}`);
    row('settled text', `medoid reader ${pg.diplomatic.reader}, run ${pg.diplomatic.run_id}, prompt sha256 ${(pg.diplomatic.prompt_sha256 || '').slice(0, 12)}…, ${pg.diplomatic.path}`);
    row('consensus', `run ${pg.consensus.run_id} · ${pg.consensus.readers.join(', ')} · agreement ${pg.consensus.agreement} · ${pg.consensus.spans} spans, ${pg.consensus.check_in} to check (weight ≥ ${pg.consensus.min_weight})${pg.consensus.medoid_cer_norm != null ? ' · medoid normalised CER ' + pg.consensus.medoid_cer_norm : ''}`);
    if (pg.anchors) row('anchors', `${pg.anchors.segmentation.reader} (${pg.anchors.segmentation.polygons} polygons, ${pg.anchors.segmentation.path}) · max distance ${pg.anchors.max_dist} · ${pg.anchors.matched} matched, ${pg.anchors.merged} merged, ${pg.anchors.split} split, ${pg.anchors.unanchored} unanchored`);
    if (hasTranslation(pg)) row('translation', `run ${pg.translation.run_id} · ${pg.translation.models.join(' vs ')} · divergence threshold ${pg.translation.min_divergence} · ${pg.translation.blocks.length} blocks${Object.values(pg.translation.uncovered || {}).some(u => u.length) ? ' · uncovered lines: ' + Object.entries(pg.translation.uncovered).map(([m, u]) => `${short(m)} ${u.join(' ')}`).join('; ') : ''}`);
    row('normalisation', `evaluate.normalize sha256 ${(DATA.normalize_sha256 || '').slice(0, 12)}… (ſ→s, superscript umlauts, hyphenation, whitespace; spans were computed on it)`);
    row('log', `${DATA.paths.log} · ${(DATA.log || []).length} events at build time`);
    inner.append(t); d.append(inner); footEl.append(d);
  }

  // ---------- hover, selection, navigation ----------
  function hot(ids) {
    $$('.fig rect.hot', workEl).forEach(r => r.classList.remove('hot'));
    $$('.ln.hot, .seg.hot', workEl).forEach(n => n.classList.remove('hot'));
    for (const id of ids) { $$(`.fig rect[data-line="${id}"]`, workEl).forEach(r => r.classList.add('hot')); $$(`.ln[data-line="${id}"]`, workEl).forEach(n => n.classList.add('hot')); }
    $$('.seg[data-lines]', workEl).forEach(s => { if (s.dataset.lines.split(' ').some(x => ids.includes(x))) s.classList.add('hot'); });
  }
  function selRects(ids) { $$('.fig rect.sel', workEl).forEach(r => r.classList.remove('sel')); for (const id of ids) $$(`.fig rect[data-line="${id}"]`, workEl).forEach(r => r.classList.add('sel')); }
  function goTo(pid, lines) {
    const i = pages.findIndex(p => p.page_id === pid);
    if (i >= 0 && i !== pageIdx) { pageIdx = i; prefs.page = pid; savePrefs(); history.replaceState(null, '', '#' + encodeURIComponent(pid)); renderBar(); renderWork(); renderFoot(); }
    const first = $(`.ln[data-line="${lines[0]}"]`, workEl) || $(`.seg[data-lines~="${lines[0]}"]`, workEl);
    if (first) first.scrollIntoView({ block: 'center', behavior: 'smooth' });
    for (const id of lines) { $$(`.fig rect[data-line="${id}"], .ln[data-line="${id}"]`, workEl).forEach(n => { n.classList.remove('flash'); void n.offsetWidth; n.classList.add('flash'); setTimeout(() => n.classList.remove('flash'), 1700); }); }
  }
  let floatEl = null, popEl = null, currentSel = null;
  const hideFloat = () => { if (floatEl) { floatEl.remove(); floatEl = null; } };
  const closePop = () => { if (popEl) { popEl.remove(); popEl = null; } };
  function selectionInfo() {
    const s = getSelection(); if (!s || s.isCollapsed || !s.rangeCount) return null;
    const r = s.getRangeAt(0); const pane = $('.rr-text', workEl); if (!pane || !pane.contains(r.commonAncestorContainer)) return null;
    const nodes = $$('.ln, .seg', pane).filter(n => r.intersectsNode(n)); if (!nodes.length) return null;
    const layer = nodes.every(n => n.classList.contains('seg')) ? 'translation' : 'transcription';
    const picked = nodes.filter(n => n.classList.contains(layer === 'translation' ? 'seg' : 'ln'));
    const lines = uniq(picked.flatMap(n => n.classList.contains('ln') ? [n.dataset.line] : n.dataset.lines.split(' ').filter(Boolean)));
    const pg = page(); let quote = s.toString().replace(/\s+\n/g, '\n').trim();
    if (layer === 'translation') for (const n of picked) for (const x of n.querySelectorAll('.tag, .note, button')) quote = quote.replace(x.textContent, '').trim();
    const info = { doc: pg.doc_id, page: pg.page_id, layer, lines, segment: null, block: layer === 'translation' ? (picked[0].dataset.block || null) : null, start: null, end: null, quote };
    if (layer === 'transcription' && picked.length) {
      const f = picked[0], l = picked[picked.length - 1];
      const so = f.contains(r.startContainer) ? offsetWithin(f, r.startContainer, r.startOffset) : 0;
      const eo = l.contains(r.endContainer) ? offsetWithin(l, r.endContainer, r.endOffset) : l.textContent.length;
      info.start = { line: f.dataset.line, char: so }; info.end = { line: l.dataset.line, char: eo };
      // the quote is cut from the lines themselves, so nothing outside the text (the ✎ button) can leak in
      const texts = picked.map(n => n.textContent.replace(/ /g, ''));
      info.quote = (picked.length === 1 ? texts[0].slice(so, eo) : [texts[0].slice(so), ...texts.slice(1, -1), texts[texts.length - 1].slice(0, eo)].join('\n')).trim();
    }
    return { info, rect: r.getBoundingClientRect(), block: layer === 'translation' && pg.translation ? pg.translation.blocks.find(b => b.block_id === info.block) : null };
  }
  let selTimer = null;
  document.addEventListener('selectionchange', () => { clearTimeout(selTimer); selTimer = setTimeout(onSelection, 140); });
  function onSelection() {
    if (popEl) return;
    const si = selectionInfo();
    if (!si) { selRects([]); hideFloat(); currentSel = null; return; }
    currentSel = si; selRects(si.info.lines); showFloat(si);
  }
  function showFloat(si) {
    hideFloat();
    const f = el('div', 'rr-float'); f.setAttribute('role', 'toolbar'); f.addEventListener('mousedown', e => e.preventDefault());
    const b = (t, fn, title) => { const x = el('button', '', t); x.onclick = fn; if (title) x.title = title; f.append(x); return x; };
    b('Issue', () => openNote('issue', si.info, f), 'Something is wrong here; log it to come back to');
    b('Question', () => openNote('question', si.info, f), 'Something to ask or look up');
    b('Comment', () => openNote('comment', si.info, f), 'A note on this passage');
    f.append(el('span', 'sep'));
    b('Copy', () => copyOut('text', si), 'Copy the selected text');
    b('Cite', () => copyOut('plain', si), 'Copy the passage with its citation');
    b('Markdown', () => copyOut('markdown', si), 'Blockquote with a footnote citation');
    b('CSL-JSON', () => copyOut('csl', si), 'For Zotero: Import from Clipboard');
    document.body.append(f); floatEl = f;
    const w = f.offsetWidth, left = Math.max(8, Math.min(window.innerWidth - w - 8, si.rect.left)), top = si.rect.bottom + 8 > window.innerHeight - 50 ? si.rect.top - f.offsetHeight - 8 : si.rect.bottom + 8;
    f.style.left = left + 'px'; f.style.top = Math.max(8, top) + 'px';
  }
  async function copyOut(format, si) {
    const pg = page(); const c = citeFor(pg, si.info.lines, si.info.layer, si.info.quote, si.block);
    const text = format === 'text' ? si.info.quote : format === 'plain' ? `“${si.info.quote}” — ${c.plain}` : format === 'markdown' ? c.markdown : c.csl_json;
    let ok = false;
    try { await navigator.clipboard.writeText(text); ok = true; } catch (_) { ok = false; }
    if (format !== 'text') store.add(mk('excerpt', si.info, { format, text: si.info.quote, citation: format === 'csl' ? c.csl : c.plain }));
    if (ok) toast(format === 'text' ? 'Copied.' : format === 'csl' ? 'CSL-JSON copied. In Zotero: File → Import from Clipboard.' : 'Copied with citation.');
    else { openPop(si.rect, pop => { pop.append(el('h3', '', 'Copy this'), (() => { const p = el('pre', '', text); return p; })(), el('p', 'hint', 'The browser would not write to the clipboard; select and copy from here.')); }); }
  }
  function openPop(rect, fill) {
    closePop(); hideFloat();
    const pop = el('div', 'rr-pop'); pop.setAttribute('role', 'dialog'); pop.addEventListener('mousedown', e => e.stopPropagation());
    fill(pop);
    const acts = pop.querySelector('.actions') || el('div', 'actions'); if (!acts.parentElement) pop.append(acts);
    const cancel = el('button', '', 'Close'); cancel.onclick = closePop; acts.prepend(cancel);
    document.body.append(pop); popEl = pop;
    const w = pop.offsetWidth, h = pop.offsetHeight;
    let left = Math.max(8, Math.min(window.innerWidth - w - 8, rect.left)), top = rect.bottom + 10; if (top + h > window.innerHeight - 10) top = Math.max(8, rect.top - h - 10);
    pop.style.left = left + 'px'; pop.style.top = top + 'px';
    const first = pop.querySelector('textarea, input[type=text], input[type=radio]'); if (first) first.focus();
  }
  function openNote(type, anchor, near, ref) {
    const rect = near.getBoundingClientRect ? near.getBoundingClientRect() : near;
    openPop(rect, pop => {
      pop.append(el('h3', '', { issue: 'Mark an issue', question: 'Ask a question', comment: ref ? 'Reply' : 'Add a comment' }[type]));
      if (anchor && anchor.quote) pop.append(el('div', 'q', anchor.quote));
      const ta = el('textarea'); ta.rows = 3; ta.placeholder = type === 'issue' ? 'What is wrong, or what to check' : type === 'question' ? 'What you want to know or look up' : 'Your note'; pop.append(ta);
      const acts = el('div', 'actions'); const save = el('button', 'primary', 'Save to log'); save.onclick = () => { if (!ta.value.trim()) { ta.focus(); return; } store.add(mk(type, anchor, { text: ta.value.trim() }, ref)); closePop(); getSelection().removeAllRanges(); toast('Logged.'); }; acts.append(save); pop.append(acts);
    });
  }
  function openSpanDecision(pg, l, sp, markEl) {
    const orig = l.settled.slice(sp.start, sp.end);
    openPop(markEl.getBoundingClientRect(), pop => {
      pop.append(el('h3', '', `Readers disagree here · ${Object.keys(sp.alternatives).length} of ${pg.consensus.readers.length - 1} differ · weight ${(sp.weight || 0).toFixed(2)}`));
      pop.append(el('div', 'q', l.settled));
      if (sp.of > 1) pop.append(el('p', 'hint', `This passage runs across ${sp.of} lines; the decision text is placed on its first part.`));
      const name = 'd' + sp.span_id; let chosen = { choice: 'keep', reader: null, text: orig };
      const opt = (label, t, value, reader) => { const lab = el('label', 'opt'); const r = el('input'); r.type = 'radio'; r.name = name; r.value = value; if (value === 'keep') r.checked = true; r.onchange = () => { chosen = { choice: value, reader, text: t }; }; const box = el('span'); box.append(el('span', 'r', label), el('span', 't', t === '' ? '(nothing: the readers have no text here)' : t)); lab.append(r, box); pop.append(lab); };
      opt(`keep the medoid (${short(pg.diplomatic.reader)})`, orig, 'keep', null);
      for (const [k, v] of Object.entries(sp.alternatives)) opt(short(k), v, 'alt', k);
      const lab = el('label', 'opt'); const r = el('input'); r.type = 'radio'; r.name = name; r.value = 'custom'; const inp = el('input'); inp.type = 'text'; inp.placeholder = 'your own reading (ſ and old spelling welcome)'; inp.oninput = () => { r.checked = true; chosen = { choice: 'custom', reader: null, text: inp.value }; }; r.onchange = () => { chosen = { choice: 'custom', reader: null, text: inp.value }; inp.focus(); }; const box = el('span'); box.style.flex = '1'; box.append(el('span', 'r', 'other'), inp); lab.append(r, box); pop.append(lab);
      const note = el('textarea'); note.rows = 2; note.placeholder = 'why (optional)'; pop.append(note);
      pop.append(el('p', 'hint', 'Alternatives are shown as the consensus normalised them (ſ as s). Your decision is recorded as an event; the text itself changes when apply and build are run.'));
      const acts = el('div', 'actions'); const save = el('button', 'primary', 'Record decision'); save.onclick = () => {
        if (chosen.choice === 'custom' && !inp.value.trim()) { inp.focus(); return; }
        const anchor = { doc: pg.doc_id, page: pg.page_id, layer: 'transcription', lines: [l.line_id], segment: null, block: null, start: { line: l.line_id, char: sp.start }, end: { line: l.line_id, char: sp.end }, quote: orig };
        store.add(mk('decision', anchor, { target: `span:${pg.page_id}:${sp.span_id}`, choice: chosen.choice, reader: chosen.reader, text: chosen.choice === 'custom' ? inp.value : chosen.text, note: note.value.trim() })); closePop(); toast('Decision recorded.');
      }; acts.append(save); pop.append(acts);
    });
  }
  function openLineDecision(pg, l, near) {
    const dec = decisions(); const cur = (dec[`line:${pg.page_id}:${l.line_id}`] || {}).body; const text = cur ? cur.text : l.settled;
    openPop(near.getBoundingClientRect(), pop => {
      pop.append(el('h3', '', `Replace line ${l.line_id}`), el('p', 'hint', 'The medoid reading of this line is below; edit it to what the page says. The diplomatic text is kept; your version becomes the settled text at the next apply.'));
      const ta = el('textarea', 'src'); ta.rows = 3; ta.value = text; pop.append(ta);
      const note = el('textarea'); note.rows = 2; note.placeholder = 'why (optional)'; pop.append(note);
      const acts = el('div', 'actions'); const save = el('button', 'primary', 'Record decision'); save.onclick = () => { store.add(mk('decision', { doc: pg.doc_id, page: pg.page_id, layer: 'transcription', lines: [l.line_id], segment: null, block: null, start: { line: l.line_id, char: 0 }, end: { line: l.line_id, char: l.settled.length }, quote: l.settled }, { target: `line:${pg.page_id}:${l.line_id}`, choice: 'custom', reader: null, text: ta.value, note: note.value.trim() })); closePop(); toast('Decision recorded.'); }; acts.append(save); pop.append(acts);
    });
  }
  function openBlockDecision(pg, b, near) {
    const [ma, mb] = pg.translation.models;
    openPop(near.getBoundingClientRect(), pop => {
      pop.append(el('h3', '', `Translation of ${b.lines.join(' ')}`));
      pop.append(el('div', 'q', b.lines.map(id => (pg.lines.find(l => l.line_id === id) || {}).settled || '').join('\n')));
      let chosen = { choice: 'a', text: (b.a || {}).text || '' }; const name = 'b' + b.block_id;
      const opt = (label, t, value) => { const lab = el('label', 'opt'); const r = el('input'); r.type = 'radio'; r.name = name; r.value = value; if (value === 'a') r.checked = true; r.onchange = () => { chosen = { choice: value, text: t }; }; const box = el('span'); box.append(el('span', 'r', label), el('span', 't', t)); lab.append(r, box); pop.append(lab); };
      if (b.a) opt(short(ma), b.a.text, 'a'); if (b.b) opt(short(mb), b.b.text, 'b');
      const lab = el('label', 'opt'); const r = el('input'); r.type = 'radio'; r.name = name; r.value = 'custom'; const ta = el('textarea'); ta.rows = 3; ta.placeholder = 'your own translation'; ta.oninput = () => { r.checked = true; chosen = { choice: 'custom', text: ta.value }; }; r.onchange = () => { chosen = { choice: 'custom', text: ta.value }; ta.focus(); }; const box = el('span'); box.style.flex = '1'; box.append(el('span', 'r', 'other'), ta); lab.append(r, box); pop.append(lab);
      const note = el('textarea'); note.rows = 2; note.placeholder = 'why (optional)'; pop.append(note);
      const acts = el('div', 'actions'); const save = el('button', 'primary', 'Record decision'); save.onclick = () => { if (chosen.choice === 'custom' && !ta.value.trim()) { ta.focus(); return; } store.add(mk('decision', { doc: pg.doc_id, page: pg.page_id, layer: 'translation', lines: b.lines, segment: null, block: b.block_id, start: null, end: null, quote: (b.a || b.b || {}).text || '' }, { target: `block:${pg.page_id}:${b.block_id}`, choice: chosen.choice, reader: chosen.choice === 'a' ? ma : chosen.choice === 'b' ? mb : null, text: chosen.choice === 'custom' ? ta.value : chosen.text, note: note.value.trim() })); closePop(); toast('Decision recorded.'); }; acts.append(save); pop.append(acts);
    });
  }
  function goPage(i) {
    if (i < 0 || i >= pages.length) return;
    pageIdx = i; prefs.page = pages[i].page_id; savePrefs();
    history.replaceState(null, '', '#' + encodeURIComponent(pages[i].page_id));
    renderBar(); renderWork(); renderFoot();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  function openAddSource(near) {
    openPop(near.getBoundingClientRect(), pop => {
      pop.append(el('h3', '', 'Bringing another document into this room'));
      pop.append(el('p', 'hint', 'A source arrives here after it has been through the bake-off with a hybrid reader and the consensus step (02-your-project/README.md has those commands). Then, from the repository root:'));
      pop.append(el('pre', '', [
        `uv run python -m mueser.reading collect --case ${DATA.case} \\`,
        `  --consensus <outputs/consensus/consensus.json> --runs <outputs/runs/<run_id>> --pages <inputs/pages> --segmentation "hybrid:*"`,
        `uv run python -m mueser.reading init-doc --pages <inputs/my-source> --out ${DATA.case}/inputs/metadata.json`,
        `uv run python -m mueser.reading settle --case ${DATA.case}`,
        `uv run python -m mueser.reading translate --case ${DATA.case}`,
        `uv run python -m mueser.reading build --case ${DATA.case}`,
      ].join('\n')));
      pop.append(el('p', 'hint', 'init-doc writes the page ids; the title, author, date, place, publisher and archive in metadata.json are yours to fill, and the citations come from them. The README of this case, section "Your own pages", says the same at more length.'));
    });
  }
  document.addEventListener('keydown', e => {
    const t = e.target;
    if (popEl || (t && typeof t.matches === 'function' && t.matches('input, textarea, select'))) return;
    if (e.key === 'ArrowRight' && !e.altKey && !e.metaKey && !e.ctrlKey) goPage(pageIdx + 1);
    if (e.key === 'ArrowLeft' && !e.altKey && !e.metaKey && !e.ctrlKey) goPage(pageIdx - 1);
  });
  let toastTimer = null;
  function toast(msg) { let t = $('.rr-toast'); if (!t) { t = el('div', 'rr-toast'); t.setAttribute('role', 'status'); document.body.append(t); } t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, msg.length > 60 ? 9000 : 2600); }
  document.addEventListener('mousedown', e => { if (popEl && !popEl.contains(e.target)) closePop(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { closePop(); hideFloat(); } });
  window.addEventListener('hashchange', () => { const pid = decodeURIComponent(location.hash.slice(1)); const i = pages.findIndex(p => p.page_id === pid); if (i >= 0 && i !== pageIdx) { pageIdx = i; renderBar(); renderWork(); renderFoot(); } });

  // ---------- boot ----------
  store.load();
  renderAll();
  store.ping().then(() => { renderBar(); renderWork(); });
})();
