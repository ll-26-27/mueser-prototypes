/* Thinkers and events: the page draws itself from the JSON block.
   One node is chosen at a time. Above it, the band of periods and events that overlap the view; below, three
   columns: what came before it (left), the node itself with its overview, works, references and connection
   map (centre), and what it touched (right). Layers choose which classes of connection are shown
   (thinkers to thinkers, thinkers to events, works to works, …) and whose connections: the record (Wikidata),
   the model's reading of the extracts, or the people using this page. Every decision, note and excerpt is an
   event in the log. */
(function () {
  'use strict';
  const D = JSON.parse(document.getElementById('timeline-data').textContent);
  const N = new Map(D.nodes.map(n => [n.id, n]));
  const ET = D.edge_types || {};
  const bySrc = new Map(), byDst = new Map(), E = new Map();
  for (const e of D.edges) { E.set(e.id, e); push(bySrc, e.src, e); push(byDst, e.dst, e); }
  function push(m, k, v) { if (!m.has(k)) m.set(k, []); m.get(k).push(v); }

  const $ = (s, r) => (r || document).querySelector(s);
  const el = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const svgEl = (tag, attrs) => { const x = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const k in attrs || {}) x.setAttribute(k, attrs[k]); return x; };
  const fold = s => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const fmtYear = y => y == null ? '?' : (y < 0 ? `${-y} BCE` : String(y));
  const span = n => n.sy == null ? '' : (n.ey != null && n.ey !== n.sy ? `${fmtYear(n.sy)}–${fmtYear(n.ey)}` : fmtYear(n.sy));
  const bucket = t => (t === 'period' ? 'event' : t);
  const ORDER = { person: 0, work: 1, event: 2, concept: 3 };
  const TYPE_NAME = { person: 'Thinker', work: 'Work', event: 'Event', period: 'Period', concept: 'Concept' };
  const persp = e => e.source.startsWith('wikidata') ? 'record' : e.source.startsWith('model') ? 'model' : 'person';
  const PERSP = { record: 'The record (Wikidata statements)', model: 'The model’s reading of the Wikipedia extracts', person: 'Added in this page' };
  function cls(e) {
    const a = bucket(N.get(e.src)?.type || ''), b = bucket(N.get(e.dst)?.type || '');
    return ORDER[a] <= ORDER[b] ? `${a}–${b}` : `${b}–${a}`;
  }
  const CLASSES = {}; for (const e of D.edges) { const c = cls(e); CLASSES[c] = (CLASSES[c] || 0) + 1; }
  const CLASS_NAME = { 'person–person': 'Thinkers to thinkers', 'person–event': 'Thinkers to events', 'person–work': 'Thinkers to works',
    'person–concept': 'Thinkers to concepts', 'work–work': 'Works to works', 'work–event': 'Works to events', 'work–concept': 'Works to concepts',
    'event–event': 'Events to events', 'event–concept': 'Events to concepts', 'concept–concept': 'Concepts to concepts' };

  // Where an edge appears for the chosen node S: 'in' (left), 'out' (right), 'events' / 'people' / 'about' (middle right),
  // 'works' / 'schools' (centre lists). First entry: S is the edge's src; second: S is its dst.
  const PLACE = {
    influenced_by: ['in', 'out'], student_of: ['in', 'out'], doctoral_advisor: ['in', 'out'], teacher_of: ['out', 'in'], doctoral_student: ['out', 'in'],
    author: ['in', 'works'], notable_work: ['works', 'in'], member_of_movement: ['schools', 'people'], field_of_work: ['schools', 'people'],
    main_subject: ['about', 'out'], part_of: ['in', 'out'], follows: ['in', 'out'], followed_by: ['out', 'in'], has_cause: ['in', 'out'], has_effect: ['out', 'in'],
    significant_event: ['events', 'people'], participant_in: ['events', 'people'], participant: ['people', 'events'],
    lived_through: ['events', 'people'], took_part_in: ['events', 'people'], wrote_in_response_to: ['events', 'people'],
    suffered_under: ['events', 'people'], shaped_by: ['events', 'people'],
  };
  const INV = { influenced_by: 'influenced', student_of: 'taught', doctoral_advisor: 'supervised', teacher_of: 'student of', doctoral_student: 'advised by',
    author: 'work', notable_work: 'author', member_of_movement: 'member', field_of_work: 'worked on by', main_subject: 'treated in', part_of: 'contains',
    follows: 'followed by', followed_by: 'follows', has_cause: 'led to', has_effect: 'caused by', significant_event: 'significant for',
    participant_in: 'participant', participant: 'took part in', lived_through: 'lived through by', took_part_in: 'participant',
    wrote_in_response_to: 'answered by', suffered_under: 'bore on', shaped_by: 'shaped' };
  const HEAD = {
    in: { person: 'Influenced by', work: 'Author and influences', event: 'Context', period: 'Context', concept: 'Influenced by' },
    mid: { person: 'Events', event: 'People', period: 'People', work: 'About', concept: 'Thinkers' },
    out: { person: 'Influenced', work: 'Influenced', event: 'Outcome', period: 'Outcome', concept: 'Works and followers' },
  };
  const MID = { person: 'events', event: 'people', period: 'people', work: 'about', concept: 'people' };
  const EDGE_COLOR = { 'person–person': '#2a5fb0', 'person–event': '#b03a2a', 'person–work': '#8a5a2a', 'person–concept': '#2f7d4f', 'work–work': '#8a5a2a',
    'work–event': '#b03a2a', 'work–concept': '#2f7d4f', 'event–event': '#5e5e5e', 'event–concept': '#2f7d4f', 'concept–concept': '#2f7d4f' };

  // ------------------------------------------------------------------ state, store
  const state = { sel: null, win: [1500, 1700], layers: new Set(Object.keys(CLASS_NAME)), persp: new Set(['record', 'model', 'person']),
    showRejected: false, logOpen: false, who: '', online: false, serverEvents: 0, logFilter: { type: '', status: '' } };
  // Keep unsent notes available when this case is rebuilt with a new data id.
  const KEY = 'mueser.timeline.case.' + location.pathname;
  const LEGACY_KEY = 'mueser.timeline.' + D.data_id;
  const store = {
    local: [], pending: new Set(), flushing: false, durable: true,
    load() { try { const raw = localStorage.getItem(KEY) || localStorage.getItem(LEGACY_KEY); if (raw) { const o = JSON.parse(raw); this.local = o.events || []; this.pending = new Set(o.pending || []); } } catch (_) {} },
    save() { try { localStorage.setItem(KEY, JSON.stringify({ events: this.local, pending: [...this.pending] })); this.durable = true; } catch (_) { this.durable = false; } },
    all() { const seen = new Set(), out = []; for (const e of [...(D.log || []), ...this.local]) { if (!seen.has(e.id)) { seen.add(e.id); out.push(e); } } return out; },
    async ping() {
      try { const r = await fetch('/api/ping', { cache: 'no-store' }); if (!r.ok) throw 0; const j = await r.json();
        if (!Object.prototype.hasOwnProperty.call(j, 'data_id')) throw new Error('Not a timeline server');
        state.online = true; state.serverEvents = j.events; if (j.who && !state.who) { state.who = j.who; } return true; } catch (_) { state.online = false; return false; }
    },
    async post(ev) {
      if (!state.online) { this.pending.add(ev.id); this.save(); return false; }
      try { const r = await fetch('/api/log', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(ev) });
        if (!r.ok) { const j = await r.json().catch(() => ({})); toast('Not saved: ' + (j.error || r.status)); this.pending.add(ev.id); this.save(); return false; }
        const result = await r.json(); if (!result.ok || result.id !== ev.id) throw new Error('Save not acknowledged');
        this.pending.delete(ev.id); this.save(); if (!result.duplicate) state.serverEvents++; return true; } catch (_) { state.online = false; this.pending.add(ev.id); this.save(); return false; }
    },
    async add(ev) { this.local.push(ev); this.pending.add(ev.id); this.save(); const ok = await this.post(ev); renderConn(); return ok; },
    async flush() {
      if (this.flushing) return;
      this.flushing = true;
      try { for (const id of [...this.pending]) { if (!state.online) break; const ev = this.local.find(e => e.id === id); if (ev) await this.post(ev); } }
      finally { this.flushing = false; }
    },
    async reconnect() { await this.ping(); if (state.online) await this.flush(); renderConn(); },
    exportAll() {
      const lines = this.local.map(e => JSON.stringify(e)).join('\n') + '\n';
      const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([lines], { type: 'application/x-ndjson' }));
      a.download = `timeline-log-${(state.who || 'reader').replace(/\W+/g, '-')}-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.jsonl`; a.click();
    },
  };
  function ts() { const d = new Date(), p = n => String(n).padStart(2, '0'), o = -d.getTimezoneOffset(), s = o >= 0 ? '+' : '-';
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}${s}${p(Math.floor(Math.abs(o) / 60))}${p(Math.abs(o) % 60)}`; }
  function uid() { const h = (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(16).slice(2) + Date.now().toString(16)).replace(/-/g, ''); return 'evt_' + h; }
  function mk(type, anchor, body, ref) { return { id: uid(), ts: ts(), who: state.who || '', client: 'timeline.html', data_id: D.data_id, type, anchor: anchor || undefined, body: body || {}, ref: ref || undefined }; }

  function decisions() { const out = new Map(); for (const e of store.all()) if (e.type === 'decision' && e.anchor?.edge) out.set(e.anchor.edge, e); return out; }
  function statusOf(e) { const d = decisions().get(e.id); if (d) return d.body.choice === 'accept' ? 'accepted' : d.body.choice === 'reject' ? 'rejected' : e.status; return e.status; }
  function personEdges() {
    const out = [];
    for (const ev of store.all()) if (ev.type === 'edge' && ev.body.src && ev.body.dst && ev.body.type && N.has(ev.body.src) && N.has(ev.body.dst)) {
      const id = `${ev.body.type}:${ev.body.src}:${ev.body.dst}`;
      if (!E.has(id) && !out.some(x => x.id === id)) out.push({ id, type: ev.body.type, src: ev.body.src, dst: ev.body.dst, source: `person:${ev.who || 'unnamed'}`, status: 'person', reason: ev.body.reason || '', evidence: ev.body.evidence || '', event: ev.id });
    }
    return out;
  }
  function classCounts() {
    const counts = { ...CLASSES };
    for (const edge of personEdges()) { const key = cls(edge); counts[key] = (counts[key] || 0) + 1; }
    return counts;
  }
  function edgesOf(id) {
    const out = [...(bySrc.get(id) || []), ...(byDst.get(id) || [])];
    for (const e of personEdges()) if (e.src === id || e.dst === id) out.push(e);
    return out.filter(active);
  }
  function active(e) {
    if (!state.layers.has(cls(e))) return false;
    if (!state.persp.has(persp(e))) return false;
    if (!state.showRejected && statusOf(e) === 'rejected') return false;
    return true;
  }
  function issueStatus() { const st = new Map(); for (const e of store.all()) { if (e.type === 'issue' || e.type === 'question') st.set(e.id, 'open'); if (e.type === 'status' && e.ref) st.set(e.ref, e.body.status || 'open'); } return st; }

  // ------------------------------------------------------------------ render
  let app, bandEl, bodyEl, popEl, toastT;
  function renderAll() { app.innerHTML = ''; app.append(renderTop(), renderBand(), renderBody(), renderFoot()); }

  function renderTop() {
    const top = el('div', 'tl-top'); const bar = el('div', 'tl-bar');
    const brand = el('a', 'brand', 'Thinkers and events'); brand.href = '#'; brand.onclick = e => { e.preventDefault(); goTo(defaultNode()); };
    const small = el('small', '', `${D.nodes.length.toLocaleString()} nodes · ${D.edges.length.toLocaleString()} connections`); brand.append(small);
    bar.append(brand, el('div', 'spacer'));
    bar.append(renderPicker()); bar.append(el('div', 'spacer'));
    const layers = el('button', 'tool', 'Layers'); layers.onclick = ev => openLayers(ev.currentTarget);
    const legend = el('button', 'tool', 'Legend'); legend.onclick = ev => openLegend(ev.currentTarget);
    const who = el('label', 'tl-who'); who.append('Reading as'); const wi = el('input'); wi.value = state.who; wi.placeholder = 'your name';
    wi.onchange = () => { state.who = wi.value.trim(); try { localStorage.setItem('mueser.timeline.who', state.who); } catch (_) {} }; who.append(wi);
    const conn = el('span', 'tl-conn'); conn.id = 'tl-conn';
    const exp = el('button', 'tool', 'Export log'); exp.onclick = () => store.exportAll();
    const logb = el('button', 'tool', state.logOpen ? 'Hide log' : 'Log'); logb.onclick = () => { state.logOpen = !state.logOpen; renderAll(); };
    bar.append(layers, legend, who, conn, exp, logb); top.append(bar);
    if (!state.online) { const n = el('p', 'tl-notice'); n.append('Not connected to the local server: what you do here stays in this browser until you ', el('b', '', 'Export log'), ' and drop the file into ', el('code', '', 'outputs/timeline/inbox/'), '. Start the server with ', el('code', '', 'python -m mueser.timeline serve'), ' to save as you go.'); top.append(n); }
    setTimeout(renderConn, 0);
    return top;
  }
  function renderConn() { const c = $('#tl-conn'); if (!c) return; c.className = 'tl-conn' + (state.online ? '' : ' off');
    c.textContent = !store.durable && store.pending.size ? `Not stored in browser · ${store.pending.size} unsent · Export log before closing` : store.pending.size ? `${store.pending.size} unsent · ${state.online ? 'retrying' : 'offline'}` : state.online ? `saved to log · ${state.serverEvents} events` : `offline · ${store.local.length} here`; }

  function renderPicker() {
    const wrap = el('div', 'tl-pick'); const input = el('input'); input.type = 'text'; input.setAttribute('aria-label', 'Choose a thinker, work, event or concept');
    const cur = N.get(state.sel); input.value = cur ? cur.label : ''; input.placeholder = 'Search a thinker, work, event, concept…';
    const caret = el('span', 'caret', '▾'); wrap.append(input, caret);
    let list = null, idx = -1, items = [];
    const close = () => { if (list) { list.remove(); list = null; } };
    const open = () => {
      const q = fold(input.value.trim()); if (list) list.remove(); list = el('div', 'tl-pick-list'); idx = -1;
      items = D.nodes.filter(n => !q || fold(n.label).includes(q) || fold(n.desc).includes(q)).sort((a, b) => (fold(b.label).startsWith(q) - fold(a.label).startsWith(q)) || (b.sl_n - a.sl_n)).slice(0, 40);
      if (!items.length) list.append(el('div', 'muted', 'Nothing matches'));
      items.forEach(n => { const b = el('button'); b.type = 'button'; b.append(el('span', 't', TYPE_NAME[n.type]), el('span', '', n.label), el('span', 'y', span(n))); b.onmousedown = e => { e.preventDefault(); goTo(n.id); close(); }; list.append(b); });
      wrap.append(list);
    };
    input.onfocus = () => { input.select(); open(); }; input.oninput = open; input.onblur = () => setTimeout(close, 150);
    input.onkeydown = e => { if (!list) return; const bs = [...list.querySelectorAll('button')]; if (e.key === 'ArrowDown') { idx = Math.min(bs.length - 1, idx + 1); } else if (e.key === 'ArrowUp') { idx = Math.max(0, idx - 1); } else if (e.key === 'Enter') { e.preventDefault(); if (items[idx >= 0 ? idx : 0]) { goTo(items[idx >= 0 ? idx : 0].id); close(); input.blur(); } return; } else if (e.key === 'Escape') { close(); return; } else return;
      e.preventDefault(); bs.forEach((b, i) => b.setAttribute('aria-selected', i === idx)); bs[idx]?.scrollIntoView({ block: 'nearest' }); };
    return wrap;
  }

  // ---------------- the band
  function defaultWindow(n) {
    if (!n || n.sy == null) return [1500, 1800];
    if (n.type === 'person') { const e = n.ey != null ? n.ey : n.sy + 80; return [n.sy - 30, e + 30]; }
    if (n.type === 'work') { const a = authorsOf(n)[0]; if (a && a.sy != null) return [a.sy - 30, (a.ey != null ? a.ey : a.sy + 80) + 30]; return [n.sy - 80, n.sy + 80]; }
    const e = n.ey != null ? n.ey : n.sy; const w = Math.max(e - n.sy, 60); return [n.sy - w, e + w];
  }
  function authorsOf(w) { return (bySrc.get(w.id) || []).filter(e => e.type === 'author').map(e => N.get(e.dst)).filter(Boolean); }
  function worksOf(p) { return [...(byDst.get(p.id) || []).filter(e => e.type === 'author').map(e => N.get(e.src)), ...(bySrc.get(p.id) || []).filter(e => e.type === 'notable_work').map(e => N.get(e.dst))].filter((w, i, a) => w && a.indexOf(w) === i).sort((a, b) => (a.sy ?? 9999) - (b.sy ?? 9999)); }

  function renderBand() {
    bandEl = el('div', 'tl-band');
    const S = N.get(state.sel); const [y0, y1] = state.win; const W = Math.max(600, app.clientWidth || window.innerWidth); const padL = 24, padR = 24;
    const x = y => padL + (y - y0) / (y1 - y0) * (W - padL - padR);
    const connected = new Set(S ? edgesOf(S.id).map(e => e.src === S.id ? e.dst : e.src) : []);
    const overlaps = n => n.sy != null && n.sy <= y1 && (n.ey != null ? n.ey : n.sy) >= y0;
    const periods = D.nodes.filter(n => (n.type === 'period' || (n.type === 'concept' && n.ey != null)) && overlaps(n)).sort((a, b) => (connected.has(b.id) - connected.has(a.id)) || b.sl_n - a.sl_n).slice(0, 6);
    const events = D.nodes.filter(n => n.type === 'event' && overlaps(n) && n.id !== state.sel).sort((a, b) => (connected.has(b.id) - connected.has(a.id)) || b.sl_n - a.sl_n).slice(0, 14);
    if (S && (S.type === 'event') && !events.includes(S)) events.unshift(S);
    const pack = items => { const lanes = []; items.sort((a, b) => a.sy - b.sy).forEach(n => { const s = x(n.sy), e = Math.max(x(n.ey != null ? n.ey : n.sy), s + 8); let i = lanes.findIndex(l => l.end + 6 < s); if (i < 0) { lanes.push({ end: e, items: [] }); i = lanes.length - 1; } lanes[i].end = Math.max(lanes[i].end, e); lanes[i].items.push(n); }); return lanes; };
    const pl = pack(periods.slice()), evl = pack(events.slice());
    const laneH = 34, top = 18; let y = top;
    const H = top + (pl.length + evl.length) * laneH + 56 + 96;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'img', 'aria-label': 'Timeline band' });
    const drawLanes = (lanes, isPeriod) => lanes.forEach(l => { l.items.forEach(n => {
      const s = Math.max(padL - 400, x(n.sy)), e = Math.min(W - padR + 400, Math.max(x(n.ey != null ? n.ey : n.sy), s + 8)); const g = svgEl('g', { class: 'bar-g' }); g.setAttribute('tabindex', '0');
      const r = svgEl('rect', { class: 'bar' + (n.id === state.sel ? ' hi' : connected.has(n.id) ? ' connected' : ''), x: s, y, width: e - s, height: laneH - 8, rx: 1 }); g.append(r);
      const w = Math.min(e, W - padR) - Math.max(s, padL); if (w > 60) { const t = svgEl('text', { x: Math.max(s, padL) + 10, y: y + laneH / 2 + 1 }); t.textContent = w > 140 ? n.label : n.label.slice(0, Math.max(3, Math.floor(w / 9))) + (n.label.length > w / 9 ? '…' : ''); g.append(t);
        if (w > 230 + n.label.length * 7) { const yr = svgEl('text', { class: 'yrs', x: Math.min(e, W - padR) - 10, y: y + laneH / 2 + 1, 'text-anchor': 'end' }); yr.textContent = span(n); g.append(yr); } }
      const title = svgEl('title'); title.textContent = `${n.label} (${span(n)}) · ${TYPE_NAME[n.type]}`; g.append(title);
      g.onclick = () => goTo(n.id); g.onkeydown = ev => { if (ev.key === 'Enter') goTo(n.id); }; svg.append(g); }); y += laneH; });
    drawLanes(pl, true); drawLanes(evl, false);
    // axis
    y += 14; const ax = svgEl('g', { class: 'axis' }); const step = niceStep(y1 - y0);
    for (let t = Math.ceil(y0 / step) * step; t <= y1; t += step) { const tx = x(t); ax.append(svgEl('line', { x1: tx, x2: tx, y1: y + 18, y2: y + 30 })); const l = svgEl('text', { x: tx, y: y + 12, 'text-anchor': 'middle' }); l.textContent = fmtYear(t); ax.append(l); }
    ax.append(svgEl('line', { x1: padL, x2: W - padR, y1: y + 30, y2: y + 30 })); svg.append(ax); y += 40;
    // the chosen node's span
    if (S) {
      const g = svgEl('g', { class: 'life' }); let a = S, label0 = 'Born', label1 = 'Died';
      if (S.type === 'work') { const au = authorsOf(S)[0]; if (au && au.sy != null) a = au; }
      if (a.type !== 'person') { label0 = a.pt ? '' : 'Began'; label1 = 'Ended'; }
      if (a.sy != null) {
        const s = x(a.sy), e = a.ey != null ? x(a.ey) : (a.type === 'person' ? x(a.sy + 80) : s);
        if (a.type !== 'person' && a.ey != null && a.ey !== a.sy) g.append(svgEl('rect', { x: s, y: y + 2, width: e - s, height: 18 }));
        g.append(svgEl('line', { x1: s, x2: e, y1: y + 11, y2: y + 11, 'stroke-dasharray': a.ey == null && a.type === 'person' ? '3 3' : '' }));
        g.append(svgEl('circle', { cx: s, cy: y + 11, r: 6 })); const t0 = svgEl('text', { x: s, y: y + 36, 'text-anchor': 'middle' }); t0.textContent = `${label0} (${fmtYear(a.sy)})`.replace(/^ \(/, '('); g.append(t0);
        if (a.ey != null) { g.append(svgEl('circle', { cx: e, cy: y + 11, r: 6 })); const t1 = svgEl('text', { x: e, y: y + 36, 'text-anchor': 'middle' }); t1.textContent = `${label1} (${fmtYear(a.ey)})`; g.append(t1); }
        if (a.type === 'person') { const ws = worksOf(a).filter(w => w.sy != null); ws.forEach((w, i) => { const wx = x(w.sy); const tg = svgEl('g', { class: 'work-tick' }); tg.append(svgEl('line', { x1: wx, x2: wx, y1: y + 46, y2: y + 60 + (w.id === state.sel ? 6 : 0) })); if (ws.length <= 10) { const tl = svgEl('text', { x: wx, y: y + 74, 'text-anchor': 'middle' }); tl.textContent = w.label.length > 22 ? w.label.slice(0, 21) + '…' : w.label; tg.append(tl); } const tt = svgEl('title'); tt.textContent = `${w.label} (${fmtYear(w.sy)})`; tg.append(tt); tg.onclick = () => goTo(w.id); g.append(tg); }); }
      }
      svg.append(g);
    }
    bandEl.append(svg);
    if (!periods.length && !events.length) bandEl.append(el('div', 'empty', 'No periods or events in this span of years'));
    const ctl = el('div', 'window-ctl'); const zoom = f => { const [a, b] = state.win, c = (a + b) / 2, w = (b - a) * f / 2; state.win = [Math.round(c - w), Math.round(c + w)]; redrawBand(); };
    const bOut = el('button', '', '−'); bOut.title = 'Zoom out'; bOut.onclick = () => zoom(1.5); const bIn = el('button', '', '+'); bIn.title = 'Zoom in'; bIn.onclick = () => zoom(1 / 1.5);
    const fit = el('button', 'wide', 'Fit'); fit.title = 'Back to this node’s span'; fit.onclick = () => { state.win = defaultWindow(S); redrawBand(); };
    ctl.append(bOut, bIn, fit); bandEl.append(ctl);
    // pan by dragging, zoom with the wheel
    let drag = null;
    bandEl.onpointerdown = ev => { if (ev.target.closest('.window-ctl')) return; drag = { x: ev.clientX, win: state.win.slice(), moved: false }; bandEl.classList.add('dragging'); bandEl.setPointerCapture(ev.pointerId); };
    bandEl.onpointermove = ev => { if (!drag) return; const dx = ev.clientX - drag.x; if (Math.abs(dx) > 3) drag.moved = true; const yrs = dx / (W - padL - padR) * (drag.win[1] - drag.win[0]); state.win = [Math.round(drag.win[0] - yrs), Math.round(drag.win[1] - yrs)]; redrawBand(); };
    bandEl.onpointerup = bandEl.onpointercancel = ev => { if (drag && drag.moved) { ev.preventDefault(); } drag = null; bandEl.classList.remove('dragging'); };
    bandEl.onclick = ev => { if (ev.target === svg || ev.target.classList.contains('axis')) { /* background */ } };
    bandEl.onwheel = ev => { if (!ev.deltaY) return; ev.preventDefault(); const [a, b] = state.win; const rect = bandEl.getBoundingClientRect(); const px = (ev.clientX - rect.left) / rect.width; const w = b - a, f = ev.deltaY > 0 ? 1.15 : 1 / 1.15; const nw = Math.max(20, Math.min(3000, w * f)); const c = a + px * w; state.win = [Math.round(c - px * nw), Math.round(c + (1 - px) * nw)]; redrawBand(); };
    return bandEl;
  }
  function niceStep(w) { const steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]; return steps.find(s => w / s <= 10) || 1000; }
  function redrawBand() { const nb = renderBand(); bandEl.replaceWith(nb); bandEl = nb; }

  // ---------------- columns
  function renderBody() {
    bodyEl = el('div', 'tl-body' + (state.logOpen ? ' with-log' : '')); const S = N.get(state.sel);
    if (!S) { bodyEl.append(el('div', 'tl-col', 'Choose a node above.')); return bodyEl; }
    const groups = { in: [], out: [], events: [], people: [], about: [], works: [], schools: [] };
    for (const e of edgesOf(S.id)) { const asSrc = e.src === S.id; const where = (PLACE[e.type] || ['out', 'in'])[asSrc ? 0 : 1]; const other = N.get(asSrc ? e.dst : e.src); if (!other) continue;
      groups[where].push({ e, other, rel: asSrc ? (ET[e.type]?.label || e.type) : (INV[e.type] || e.type) }); }
    const byYear = arr => arr.sort((a, b) => (a.other.sy ?? 9999) - (b.other.sy ?? 9999));
    for (const k in groups) byYear(groups[k]);
    const mid = MID[S.type] || 'events';
    bodyEl.append(column(HEAD.in[S.type] || 'Before', groups.in, S, '▶'), renderMain(S, groups), column(HEAD.mid[S.type] || 'Events', groups[mid], S, '▶', mid === 'events'), column(HEAD.out[S.type] || 'After', groups.out, S, '▶'));
    if (state.logOpen) bodyEl.append(renderLog());
    return bodyEl;
  }
  function column(title, items, S, arrow, withDecisions) {
    const col = el('div', 'tl-col'); const h = el('div', 'tl-col-head'); h.append(el('span', 'arrow', arrow), title, el('span', 'n', String(items.length))); col.append(h);
    if (!items.length) col.append(el('p', 'muted', 'Nothing in the chosen layers.'));
    items.forEach(({ e, other, rel }, i) => col.append(card(other, e, rel, S, i < 4, withDecisions)));
    return col;
  }
  function firstSentence(t) { if (!t) return ''; const m = t.match(/^.{40,260}?[.!?](\s|$)/); return (m ? m[0] : t.slice(0, 220)).trim(); }
  function card(n, e, rel, S, big, withDecisions) {
    const c = el('div', 'card' + (n.id === state.sel ? ' hi' : '')); const st = statusOf(e);
    if (n.img) { const im = el('img', 'thumb' + (big ? '' : ' small')); im.loading = 'lazy'; im.src = n.img; im.alt = ''; c.append(im); }
    const name = el('button', 'name', n.label); name.onclick = () => goTo(n.id); c.append(name);
    const kind = el('div', 'kind'); kind.append(el('span', 'rel', rel), ', ', TYPE_NAME[n.type].toLowerCase(), n.sy != null ? `, ${span(n)}` : ''); c.append(kind);
    if (big && n.text) c.append(el('p', 'blurb', firstSentence(n.text.t)));
    if (e.reason) c.append(el('p', 'reason', e.reason));
    if (e.evidence) { const q = el('p', 'evidence' + (e.verified === false ? ' unverified' : ''), '“' + e.evidence + '”' + (e.verified === false ? ' (not found verbatim in the extract)' : '')); c.append(q); }
    const row = el('div', 'row'); row.append(badgeFor(e, st));
    if (persp(e) === 'model' || persp(e) === 'person') {
      if (st !== 'accepted') { const a = el('button', 'ghost', 'Accept'); a.onclick = () => decide(e, 'accept', S); row.append(a); }
      if (st !== 'rejected') { const r = el('button', 'ghost', 'Reject'); r.onclick = () => decide(e, 'reject', S); row.append(r); }
    }
    const note = el('button', 'ghost', 'Note'); note.title = 'Leave an issue, a question or a comment on this connection'; note.onclick = ev => openNote(ev.currentTarget, { node: S.id, edge: e.id, quote: `${N.get(e.src)?.label} → ${N.get(e.dst)?.label} (${e.type})` }); row.append(note);
    const more = el('button', 'more', 'Read more →'); more.onclick = () => goTo(n.id); row.append(more);
    c.append(row); return c;
  }
  function badgeFor(e, st) { const p = persp(e); const b = el('span', 'badge ' + (p === 'person' ? 'person' : st)); b.textContent = p === 'record' ? 'record' : p === 'person' ? (st === 'accepted' ? 'added · accepted' : st === 'rejected' ? 'added · rejected' : 'added here') : st; b.title = p === 'record' ? `Wikidata statement (${e.source.replace('wikidata:', '')})` : p === 'model' ? `Proposed by ${e.source.replace('model:', '')} from the Wikipedia extract` : e.source; return b; }
  async function decide(e, choice, S) {
    const ev = mk('decision', { node: S.id, edge: e.id, quote: `${N.get(e.src)?.label} → ${N.get(e.dst)?.label}` }, { choice, target: `edge:${e.id}`, type: e.type, src: e.src, dst: e.dst });
    await store.add(ev); toast(choice === 'accept' ? 'Accepted' : 'Rejected'); renderAll();
  }

  function renderMain(S, groups) {
    const main = el('div', 'tl-col tl-main'); const hero = el('div', 'tl-hero');
    let fig; if (S.img) { fig = el('img', 'portrait'); fig.src = S.img; fig.alt = `Image of ${S.label} from Wikimedia Commons`; } else { fig = el('div', 'portrait none', TYPE_NAME[S.type]); }
    hero.append(fig); const words = el('div'); words.append(el('h1', '', S.label));
    words.append(el('p', 'dates', S.sy != null ? span(S) : 'undated'));
    const where = []; if (S.desc) where.push(S.desc); if (S.place?.birth) where.push(S.place.birth + (S.place.death && S.place.death !== S.place.birth ? ' – ' + S.place.death : '')); if (S.place?.at) where.push(S.place.at.join(', ')); if (S.lang) where.push(S.lang);
    words.append(el('p', 'where', where.join(' · ')));
    const sec = el('div', 'secondary');
    if (S.type === 'work') { const au = authorsOf(S); if (au.length) { sec.append(el('h3', '', 'Author')); const p = el('p'); au.forEach((a, i) => { const b = el('button', 'more', a.label); b.onclick = () => goTo(a.id); if (i) p.append(', '); p.append(b); }); sec.append(p); } }
    if (S.occ?.length) { sec.append(el('h3', '', 'Occupations, as recorded'), el('p', '', S.occ.join(', '))); }
    if (S.countries?.length) { sec.append(el('h3', '', S.type === 'person' ? 'Citizenship, as recorded' : 'Country'), el('p', '', S.countries.join(', '))); }
    if (S.inst?.length && S.type !== 'person') { sec.append(el('h3', '', 'Kind'), el('p', '', S.inst.join(', '))); }
    words.append(sec); hero.append(words); main.append(hero, el('hr', 'tl-rule'));
    const grid = el('div', 'tl-grid'); const left = el('div'), right = el('div');
    // overview
    const ov = el('section', 'overview'); ov.append(el('h3', '', 'Overview'));
    if (S.text) { const paras = S.text.t.split(/\n+/); paras.forEach(p => ov.append(el('p', '', p))); const at = el('p', 'attrib'); const a = el('a', '', `“${S.text.title}”, Wikipedia (${S.text.lang})`); a.href = S.text.url; a.target = '_blank'; a.rel = 'noopener'; at.append('From ', a, `, revision ${S.text.rev} of ${(S.text.ts || '').slice(0, 10)}, CC BY-SA 4.0. The lead section of the article, as fetched; not a claim of this page.`); ov.append(at); }
    else ov.append(el('p', 'muted', 'No Wikipedia summary was fetched for this node.'));
    const ovActions = el('div', 'row'); const cite = el('button', 'ghost', 'Cite this node'); cite.onclick = ev => openCite(ev.currentTarget, S); const note = el('button', 'ghost', 'Note'); note.onclick = ev => openNote(ev.currentTarget, { node: S.id, quote: S.label }); const addc = el('button', 'ghost', '+ Add a connection'); addc.onclick = ev => openAddEdge(ev.currentTarget, S); ovActions.append(cite, note, addc); ov.append(ovActions); left.append(ov);
    // map
    const mapSec = el('section'); mapSec.append(renderMap(S)); left.append(mapSec);
    // works
    if (S.type === 'person' || S.type === 'concept') { const ws = S.type === 'person' ? worksOf(S) : groups.out.filter(x => x.e.type === 'main_subject').map(x => x.other); const sec2 = el('section'); sec2.append(el('h3', '', S.type === 'person' ? 'Notable works' : 'Works about it')); if (ws.length) { const ul = el('ul', 'plain'); ws.forEach(w => { const li = el('li'); const b = el('button', '', w.label); b.onclick = () => goTo(w.id); li.append(b); if (w.sy != null) li.append(el('span', 'y', `(${fmtYear(w.sy)})`)); ul.append(li); }); sec2.append(ul); } else sec2.append(el('p', 'muted', 'None recorded.')); right.append(sec2); }
    // schools / era
    const schools = groups.schools.map(x => x.other); const eras = S.sy != null ? D.nodes.filter(n => n.type === 'period' && n.sy != null && n.sy <= (S.ey ?? S.sy) && (n.ey ?? n.sy) >= S.sy).sort((a, b) => b.sl_n - a.sl_n).slice(0, 4) : [];
    if (schools.length || eras.length) { const sec3 = el('section', 'inline-tags'); sec3.append(el('h3', '', 'School of thought / era')); const p = el('p'); [...schools, ...eras].forEach((n, i) => { const b = el('button', '', n.label); b.onclick = () => goTo(n.id); if (i) p.append(', '); p.append(b); }); sec3.append(p); right.append(sec3); }
    if (S.type === 'work' && groups.about.length) { const sec4 = el('section', 'inline-tags'); sec4.append(el('h3', '', 'About')); const p = el('p'); groups.about.forEach((x, i) => { const b = el('button', '', x.other.label); b.onclick = () => goTo(x.other.id); if (i) p.append(', '); p.append(b); }); sec4.append(p); right.append(sec4); }
    // references
    const refs = el('section', 'refs'); refs.append(el('h3', '', 'Where to read about it')); const ul = el('ul', 'plain');
    const groupsL = { entry: 'Reference works', article: 'Encyclopedias', text: 'Texts', record: 'Library and authority records', other: 'Data' };
    const kindOf = l => /^(entry|overview|bibliography)/.test(l.kind) ? 'entry' : l.kind === 'article' ? 'article' : /^(text|ebook|scan|editions|author)/.test(l.kind) ? 'text' : /record/.test(l.kind) ? 'record' : 'other';
    const order = ['entry', 'article', 'text', 'record', 'other'];
    order.forEach(k => { const ls = (S.links || []).filter(l => kindOf(l) === k); if (!ls.length) return; const lab = el('li'); lab.append(el('span', 'eyebrow', groupsL[k])); ul.append(lab);
      ls.forEach(l => { const li = el('li'); const a = el('a', '', l.name); a.href = l.url; a.target = '_blank'; a.rel = 'noopener'; li.append(a, el('span', 'what', l.kind + (l.scheme.startsWith('P') || l.scheme === 'wikidata' ? ` · ${l.id}` : '')));
        const c = (S.cite || []).find(c => c.scheme === l.scheme); if (c) { const b = el('button', 'ghost', 'Cite'); b.onclick = ev => openCite(ev.currentTarget, S, c.scheme); li.append(b); } ul.append(li); }); });
    refs.append(ul);
    if (S.sep) { const p = el('p', 'attrib'); p.append(`Stanford Encyclopedia entry “${S.sep.title}” by ${S.sep.authors.join('; ')}: ${S.sep.pubinfo}.`); refs.append(p); }
    const prov = el('p', 'attrib', `Node ${S.id}, admitted by rule “${S.rule}”; ${S.sl_n} Wikipedia articles. Dates and identifiers as Wikidata holds them, fetched ${D.accessed}.`); refs.append(prov);
    right.append(refs);
    grid.append(left, right); main.append(grid);
    return main;
  }

  function renderMap(S) {
    const box = el('div', 'tl-map'); const W = 640, H = 320; const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `Connections of ${S.label}` });
    const es = edgesOf(S.id).slice(0, 48); const others = []; const seen = new Set();
    es.forEach(e => { const o = N.get(e.src === S.id ? e.dst : e.src); if (o && !seen.has(o.id)) { seen.add(o.id); others.push(o); } });
    others.sort((a, b) => (ORDER[bucket(a.type)] - ORDER[bucket(b.type)]) || ((a.sy ?? 9999) - (b.sy ?? 9999)));
    const cx = W / 2, cy = H / 2 - 6, rx = W / 2 - 110, ry = H / 2 - 40; const pos = new Map([[S.id, [cx, cy]]]);
    others.forEach((o, i) => { const a = -Math.PI / 2 + (i / Math.max(others.length, 1)) * Math.PI * 2; pos.set(o.id, [cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); });
    es.forEach(e => { const p = pos.get(e.src), q = pos.get(e.dst); if (!p || !q) return; const st = statusOf(e); const l = svgEl('line', { class: 'e ' + (persp(e) === 'model' ? 'proposed' : persp(e) === 'person' ? 'personal' : '') + (st === 'rejected' ? ' rejected' : ''), x1: p[0], y1: p[1], x2: q[0], y2: q[1], stroke: EDGE_COLOR[cls(e)] || '#777' }); const t = svgEl('title'); t.textContent = `${N.get(e.src)?.label} — ${ET[e.type]?.label || e.type} → ${N.get(e.dst)?.label} (${persp(e)}, ${st})`; l.append(t); svg.append(l); });
    const node = (n, r) => { const [x, y] = pos.get(n.id); const g = svgEl('g', { class: 'n' }); g.append(svgEl('circle', { cx: x, cy: y, r, fill: getComputedStyle(document.documentElement).getPropertyValue('--' + bucket(n.type) === '' ? '#777' : `var(--${n.type})`) }));
      const t = svgEl('text', { x: x + (x < cx - 10 ? -r - 4 : x > cx + 10 ? r + 4 : 0), y: y + (Math.abs(x - cx) <= 10 ? (y < cy ? -r - 5 : r + 13) : 4), 'text-anchor': x < cx - 10 ? 'end' : x > cx + 10 ? 'start' : 'middle' }); t.textContent = n.label.length > 26 ? n.label.slice(0, 25) + '…' : n.label; g.append(t);
      const tt = svgEl('title'); tt.textContent = `${n.label} (${span(n)})`; g.append(tt); if (n.id !== S.id) g.onclick = () => goTo(n.id); svg.append(g); };
    others.forEach(o => node(o, 5)); node(S, 8);
    box.append(svg, el('div', 'cap', 'Connection map'));
    const leg = el('div', 'legend'); const seenC = new Set(es.map(cls)); [...seenC].forEach(c => { const l = el('span', 'l'); const i = el('i'); i.style.borderColor = EDGE_COLOR[c] || '#777'; l.append(i, CLASS_NAME[c] || c); leg.append(l); });
    if (es.some(e => persp(e) === 'model')) { const l = el('span', 'l'); const i = el('i'); i.style.borderColor = '#777'; i.style.borderTopStyle = 'dashed'; l.append(i, 'proposed'); leg.append(l); }
    box.append(leg);
    if (!es.length) box.append(el('p', 'muted', ' '));
    return box;
  }

  // ---------------- log
  function renderLog() {
    const panel = el('div', 'tl-log'); const h = el('div', 'tl-col-head'); h.append('Log'); panel.append(h);
    const f = el('div', 'filters'); const t = el('select'); ['', 'decision', 'edge', 'issue', 'question', 'comment', 'excerpt', 'status'].forEach(v => { const o = el('option', '', v || 'all types'); o.value = v; t.append(o); }); t.value = state.logFilter.type; t.onchange = () => { state.logFilter.type = t.value; renderAll(); };
    const s = el('select'); ['', 'open', 'resolved'].forEach(v => { const o = el('option', '', v || 'any status'); o.value = v; s.append(o); }); s.value = state.logFilter.status; s.onchange = () => { state.logFilter.status = s.value; renderAll(); };
    f.append(t, s); panel.append(f);
    const st = issueStatus(); const evs = store.all().filter(e => e.type !== 'status').filter(e => !state.logFilter.type || e.type === state.logFilter.type).filter(e => !state.logFilter.status || st.get(e.id) === state.logFilter.status).reverse();
    if (!evs.length) panel.append(el('p', 'muted', 'Nothing yet.'));
    evs.forEach(e => { const it = el('div', 'item'); const head = el('div', 'head'); head.append(el('span', 'type ' + e.type, e.type), el('span', '', e.who || 'unnamed'), el('span', '', e.ts.slice(0, 16).replace('T', ' '))); if (st.has(e.id)) head.append(el('span', 'st ' + st.get(e.id), st.get(e.id))); it.append(head);
      const b = e.body || {}; const text = e.type === 'decision' ? `${b.choice} · ${e.anchor?.quote || b.target}` : e.type === 'edge' ? `${N.get(b.src)?.label} — ${b.type} → ${N.get(b.dst)?.label}${b.reason ? ': ' + b.reason : ''}` : e.type === 'excerpt' ? `${b.scheme || ''} citation copied` : b.text || b.note || '';
      it.append(el('div', 'body', text)); if (e.anchor?.quote && e.type !== 'decision') it.append(el('div', 'muted', '“' + e.anchor.quote.slice(0, 120) + '”'));
      const row = el('div', 'row'); const nid = e.anchor?.node || b.src; if (nid && N.has(nid)) { const j = el('button', 'jump', 'Go to ' + N.get(nid).label); j.onclick = () => goTo(nid); row.append(j); }
      if (st.get(e.id) === 'open') { const r = el('button', 'jump', 'Resolve'); r.onclick = async () => { await store.add(mk('status', e.anchor, { status: 'resolved' }, e.id)); renderAll(); }; row.append(r); }
      it.append(row); panel.append(it); });
    return panel;
  }

  function renderFoot() {
    const f = el('div', 'tl-foot'); f.append(`Data ${D.data_id}: nodes and recorded connections from Wikidata (collect run ${D.collect_run}), encyclopedia and Wikipedia texts fetched ${D.accessed}`, D.proposals_run ? `, proposed connections from ${D.model || 'a model'} (run ${D.proposals_run})` : '', `. Built ${(D.built || '').slice(0, 10)}. Decisions, notes and excerpts are appended to `, el('code', '', 'outputs/timeline/log.jsonl'), '.');
    return f;
  }

  // ---------------- popovers
  function closePop() { if (popEl) { popEl.remove(); popEl = null; } }
  function placePop(anchor) { const p = popEl, r = anchor.getBoundingClientRect(); p.style.left = Math.max(8, Math.min(window.innerWidth - p.offsetWidth - 8, r.left)) + 'px'; p.style.top = Math.min(window.innerHeight - p.offsetHeight - 8, r.bottom + 6) + 'px'; }
  function pop(anchor, title) { closePop(); popEl = el('div', 'tl-pop'); popEl.setAttribute('role', 'dialog'); popEl.append(el('h4', '', title)); document.body.append(popEl); requestAnimationFrame(() => placePop(anchor)); return popEl; }
  function openNote(anchor, a) {
    const p = pop(anchor, 'Leave a note'); const typeL = el('label', '', 'Kind'); const sel = el('select'); ['issue', 'question', 'comment'].forEach(v => { const o = el('option', '', v); o.value = v; sel.append(o); }); p.append(typeL, sel);
    p.append(el('label', '', 'On'), el('p', 'sub', a.quote || N.get(a.node)?.label || '')); p.append(el('label', '', 'Text')); const ta = el('textarea'); p.append(ta);
    const act = el('div', 'actions'); const c = el('button', 'ghost', 'Cancel'); c.onclick = closePop; const s = el('button', 'primary', 'Save'); s.onclick = async () => { if (!ta.value.trim()) { ta.focus(); return; } const saved = await store.add(mk(sel.value, a, { text: ta.value.trim() })); closePop(); toast(saved ? 'Saved to the log' : store.durable ? 'Kept in this browser · not yet saved to the log' : 'Not saved · Export log before closing'); if (state.logOpen) renderAll(); }; act.append(c, s); p.append(act); ta.focus();
  }
  function openCite(anchor, S, scheme) {
    const p = pop(anchor, 'Cite'); const cs = (S.cite || []); let cur = cs.find(c => c.scheme === scheme) || cs[0]; if (!cur) { p.append(el('p', 'muted', 'No citation.')); return; }
    const sel = el('select'); cs.forEach(c => { const o = el('option', '', c.name); o.value = c.scheme; sel.append(o); }); sel.value = cur.scheme; p.append(el('label', '', 'Source'), sel);
    const pre = el('pre'); const csl = el('pre'); const show = () => { pre.textContent = cur.plain; csl.textContent = JSON.stringify(cur.csl, null, 1); }; show(); sel.onchange = () => { cur = cs.find(c => c.scheme === sel.value); show(); };
    p.append(el('label', '', 'Citation'), pre, el('label', '', 'CSL-JSON (paste into Zotero: File → Import from Clipboard)'), csl);
    const act = el('div', 'actions'); const c1 = el('button', 'ghost', 'Copy citation'); c1.onclick = () => copyOut(cur.plain, S, cur.scheme, 'plain'); const c2 = el('button', 'ghost', 'Copy CSL-JSON'); c2.onclick = () => copyOut(JSON.stringify(cur.csl), S, cur.scheme, 'csl'); const c3 = el('button', 'ghost', 'Copy as Markdown'); c3.onclick = () => copyOut(`> ${S.label}${S.sy != null ? ' (' + span(S) + ')' : ''}[^1]\n\n[^1]: ${cur.plain}`, S, cur.scheme, 'markdown'); const x = el('button', 'primary', 'Close'); x.onclick = closePop; act.append(c1, c2, c3, x); p.append(act);
  }
  async function copyOut(text, S, scheme, form) { try { await navigator.clipboard.writeText(text); toast('Copied'); } catch (_) { toast('Copy failed; select the text'); } await store.add(mk('excerpt', { node: S.id, quote: S.label }, { scheme, form, text: text.slice(0, 2000) })); }
  function openAddEdge(anchor, S) {
    const p = pop(anchor, 'Add a connection'); p.append(el('p', 'sub', `From ${S.label} to another node. It is recorded as yours (“added here”), beside the record and the model’s proposals.`));
    p.append(el('label', '', 'To')); const inp = el('input'); inp.type = 'text'; inp.placeholder = 'search…'; p.append(inp); const res = el('div', 'pick-results'); p.append(res); let target = null; const chosen = el('p', 'sub', ''); p.append(chosen);
    inp.oninput = () => { const q = fold(inp.value.trim()); res.innerHTML = ''; if (!q) return; D.nodes.filter(n => n.id !== S.id && fold(n.label).includes(q)).sort((a, b) => b.sl_n - a.sl_n).slice(0, 12).forEach(n => { const b = el('button', '', `${n.label} · ${TYPE_NAME[n.type].toLowerCase()}${n.sy != null ? ', ' + span(n) : ''}`); b.onclick = () => { target = n; chosen.textContent = `→ ${n.label}`; res.innerHTML = ''; }; res.append(b); }); };
    p.append(el('label', '', 'Type')); const sel = el('select'); Object.keys(ET).forEach(t => { const o = el('option', '', ET[t].label + (ET[t].kind === 'proposed' ? '' : ' (as the record uses it)')); o.value = t; sel.append(o); }); p.append(sel);
    p.append(el('label', '', 'Why (one sentence)')); const why = el('textarea'); p.append(why); p.append(el('label', '', 'Evidence: a quotation or a reference, with page')); const evd = el('input'); evd.type = 'text'; p.append(evd);
    const act = el('div', 'actions'); const c = el('button', 'ghost', 'Cancel'); c.onclick = closePop; const s = el('button', 'primary', 'Add'); s.onclick = async () => { if (!target) { inp.focus(); return; } await store.add(mk('edge', { node: S.id, quote: `${S.label} → ${target.label}` }, { src: S.id, dst: target.id, type: sel.value, reason: why.value.trim(), evidence: evd.value.trim() })); closePop(); toast('Connection added'); renderAll(); }; act.append(c, s); p.append(act); inp.focus();
  }
  function openLayers(anchor) {
    const counts = classCounts();
    const p = pop(anchor, 'Layers'); p.append(el('p', 'sub', 'Which connections the columns, the band and the map show.'));
    p.append(el('div', 'group eyebrow', 'By what they connect')); Object.keys(counts).sort((a, b) => counts[b] - counts[a]).forEach(c => { const l = el('label', 'check'); const i = el('input'); i.type = 'checkbox'; i.checked = state.layers.has(c); i.onchange = () => { if (i.checked) state.layers.add(c); else state.layers.delete(c); renderAll(); openLayers($('.tl-bar .tool')); }; l.append(i, `${CLASS_NAME[c] || c} `, el('span', 'muted', `(${counts[c].toLocaleString()})`)); p.append(l); });
    p.append(el('div', 'group eyebrow', 'By whose connections')); Object.keys(PERSP).forEach(k => { const l = el('label', 'check'); const i = el('input'); i.type = 'checkbox'; i.checked = state.persp.has(k); i.onchange = () => { if (i.checked) state.persp.add(k); else state.persp.delete(k); renderAll(); openLayers($('.tl-bar .tool')); }; l.append(i, PERSP[k]); p.append(l); });
    const l = el('label', 'check'); const i = el('input'); i.type = 'checkbox'; i.checked = state.showRejected; i.onchange = () => { state.showRejected = i.checked; renderAll(); openLayers($('.tl-bar .tool')); }; l.append(i, 'Show rejected proposals'); p.append(l);
    p.append(el('p', 'sub', 'A further perspective, the connections one commentator draws across these nodes, would appear here as its own line once ingested; see the README.'));
    const act = el('div', 'actions'); const all = el('button', 'ghost', 'All'); all.onclick = () => { state.layers = new Set(Object.keys(CLASS_NAME)); state.persp = new Set(Object.keys(PERSP)); renderAll(); }; const x = el('button', 'primary', 'Close'); x.onclick = closePop; act.append(all, x); p.append(act);
  }
  function openLegend(anchor) {
    const counts = classCounts();
    const p = pop(anchor, 'Legend'); p.append(el('div', 'group eyebrow', 'Nodes'));
    Object.keys(TYPE_NAME).forEach(t => { const r = el('div', 'legend-row'); r.append(el('span', 'dot ' + t), `${TYPE_NAME[t]}s`); p.append(r); });
    p.append(el('div', 'group eyebrow', 'Connections')); Object.keys(CLASS_NAME).filter(c => counts[c]).forEach(c => { const r = el('div', 'legend-row'); const i = el('i'); i.style.borderColor = EDGE_COLOR[c]; r.append(i, CLASS_NAME[c]); p.append(r); });
    p.append(el('div', 'group eyebrow', 'Standing')); [['', 'recorded: a Wikidata statement, with its property'], ['dash', 'proposed: the model read it in the Wikipedia extract; accept or reject'], ['dots', 'added here: a reader drew it, with a reason']].forEach(([k, t]) => { const r = el('div', 'legend-row'); const i = el('i', k); i.style.borderColor = '#555'; r.append(i, t); p.append(r); });
    p.append(el('div', 'group eyebrow', 'Band')); p.append(el('p', 'sub', 'Periods in the upper lanes, events below them; bars connected to the chosen node are darker, the chosen event is pale blue. Drag to move through time, scroll to zoom, Fit to return. Beneath the axis: the chosen thinker’s life with their works as ticks.'));
    const act = el('div', 'actions'); const x = el('button', 'primary', 'Close'); x.onclick = closePop; act.append(x); p.append(act);
  }
  function toast(msg) { let t = $('.tl-toast'); if (!t) { t = el('div', 'tl-toast'); document.body.append(t); } t.textContent = msg; clearTimeout(toastT); toastT = setTimeout(() => t.remove(), 1800); }

  // ---------------- navigation
  function defaultNode() { if (N.has('Q37621')) return 'Q37621'; const ps = D.nodes.filter(n => n.type === 'person').sort((a, b) => b.sl_n - a.sl_n); return ps[0]?.id || D.nodes[0]?.id; }
  function goTo(id, keepWindow) { if (!N.has(id)) return; closePop(); state.sel = id; if (!keepWindow) state.win = defaultWindow(N.get(id)); history.replaceState(null, '', '#' + id); renderAll(); window.scrollTo({ top: 0 }); }
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closePop(); });
  document.addEventListener('click', e => { if (popEl && !e.composedPath().includes(popEl) && !e.target.closest('.tl-bar .tool, .card .ghost, .row .ghost, .refs .ghost')) closePop(); });
  window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (id && id !== state.sel) goTo(id); });

  async function boot() {
    app = $('#tl-app'); store.load(); try { state.who = localStorage.getItem('mueser.timeline.who') || ''; } catch (_) {}
    await store.reconnect();
    const id = location.hash.slice(1); state.sel = N.has(id) ? id : defaultNode(); state.win = defaultWindow(N.get(state.sel));
    renderAll();
    setInterval(() => store.reconnect(), 15000);
  }
  boot();
})();
