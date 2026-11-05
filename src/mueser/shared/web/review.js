/* Progressive enhancement only: the generated research content remains intact. */
(() => {
  'use strict';
  const config = window.REVIEW_CONFIG;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const link = (text, href) => { const a = el('a', '', text); a.href = href; return a; };
  const disclosure = (title, nodes = [], cls = '') => {
    const d = el('details', cls); d.append(el('summary', '', title), ...nodes); return d;
  };
  const wrapTable = t => {
    if (t.parentElement.classList.contains('table-scroll')) return;
    const box = el('div', 'table-scroll'); box.tabIndex = 0;
    box.setAttribute('role', 'region'); box.setAttribute('aria-label', 'Scrollable evidence table');
    t.before(box); box.append(t);
  };
  const labels = {
    'real-gartenlaube-1853-p001': ['Die Gartenlaube', '1853 · Fraktur print'],
    'real-grimm-khm-1812-i-p093': ['Grimm’s fairy tales', '1812 · Fraktur print'],
    'real-schiller-musenalmanach-1796-p093': ['Schiller’s Musenalmanach', '1796 · Antiqua print'],
    'real-kaskel-to-schnorr-1864': ['Kaskel to Schnorr', '1864 · Secretary’s hand'],
    'real-schnitzler-to-beer-hofmann-1896': ['Schnitzler to Beer-Hofmann', '1896 · Private correspondence'],
    'real-poesiealbum-hedwig-1901-p02': ['Hedwig’s poetry album', '1901 · Handwritten album'],
  };
  const sourceName = id => labels[id] || (/^synth-/.test(id)
    ? [`Synthetic page ${Number(id.replace('synth-', ''))}`, 'Invented text · Rendered sample']
    : [id.replace(/^real-/, '').replaceAll('-', ' '), 'Source page']);

  document.body.classList.add('review-ui', `review-${config.kind}`);
  const top = el('nav', 'review-topbar'); top.setAttribute('aria-label', 'Project navigation');
  const brand = link('German sources', config.home); brand.className = 'review-brand';
  const topLinks = el('div', 'top-links');
  if (config.kind !== 'home') topLinks.append(link('All experiments', config.home));
  if (config.kind === 'consensus') topLinks.append(link('Compare readers', '../index.html'));
  if (config.consensus) topLinks.append(link('Review disagreements', config.consensus));
  if (config.kind === 'home') topLinks.append(el('span', 'eyebrow', 'Bok Center · Learning Lab'));
  top.append(brand, topLinks); document.body.prepend(top);
  const skip = link('Skip to content', '#review-main'); skip.className = 'skip-link'; document.body.prepend(skip);

  function makeHeader() {
    const header = $('body > header'); if (!header) return;
    header.className = 'review-header';
    const title = $('h1', header);
    const original = [...header.children].filter(n => n !== title);
    const type = {report:'Compare the readers', consensus:'Human review', layout:'Understand the page'}[config.kind];
    header.prepend(el('div', 'eyebrow', `Transcription / ${type}`));
    const lead = {
      report:'Choose a source, then compare its readers. The image and transcription sit side by side; scores, differences, and provenance are available below.',
      consensus:'Read the source beside a shared starting text. Select a highlighted passage to see the alternatives, then work through the passages that need a decision.',
      layout:'Compare how a vision model and Kraken divide the same page. Switch sources to inspect regions, line counts, and reading order.',
    }[config.kind];
    header.append(el('p', 'lead', lead), disclosure('About this experiment · methods and definitions', original, 'methodology'));
    if (config.kind === 'consensus') {
      const exports = el('div', 'collection-links');
      exports.append(link('Download review spreadsheet ↓', 'checkin.csv'), link('Full consensus data ↓', 'consensus.json'));
      header.append(exports);
    }
  }

  function prepareReport(page) {
    const imageCol = page.children[0], reading = page.children[1];
    imageCol.classList.add('source-image'); reading.classList.add('reading-column');
    const tabs = $('.tabs', reading);
    if (tabs) {
      const buttons = $$('button', tabs);
      const picker = el('label', 'reader-picker', 'Reader'); const select = el('select');
      select.setAttribute('aria-label', `Reader for ${sourceName(page.id)[0]}`);
      buttons.forEach(b => { const o = el('option', '', b.textContent); o.value = b.dataset.target; select.append(o); });
      picker.append(select); tabs.before(picker); tabs.hidden = true;
      select.addEventListener('change', () => buttons.find(b => b.dataset.target === select.value)?.click());
      // Select by this page's measured normalised error, never a mixed-corpus mean.
      const scores = buttons.map(b => {
        const pane = document.getElementById(b.dataset.target);
        const stat = $$('.stat', pane).find(s => $('b', s)?.textContent === 'cer_norm');
        return {button:b, score:stat ? Number(stat.textContent.replace('cer_norm', '').trim()) : Infinity};
      });
      const best = scores.reduce((a, b) => b.score < a.score ? b : a, scores[0]);
      if (best && Number.isFinite(best.score)) {
        select.value = best.button.dataset.target; best.button.click();
        picker.after(el('p', 'reader-note', 'Starts with the lowest measured normalised character error on this page.'));
      }
    }
    $$('.pane', reading).forEach(pane => {
      const rawDetails = $$(':scope > details', pane).find(d => $('summary', d)?.textContent === 'Output as written');
      if (rawDetails) {
        const raw = $('pre', rawDetails), diff = $(':scope > pre', pane);
        const explanation = diff?.previousElementSibling;
        const evidence = disclosure('Compare with reference text · highlighted differences');
        if (diff) { diff.before(raw); if (explanation) evidence.append(explanation); evidence.append(diff); }
        rawDetails.replaceWith(evidence);
      }
      const path = $$(':scope > p', pane).find(p => p.textContent.startsWith('output:'));
      if (path) { const details = disclosure('Source files and prompt fingerprint', [], 'provenance'); path.before(details); details.append(path); }
      const names = {cer:'Character error', cer_norm:'Normalised error', wer:'Word error', wer_norm:'Normalised word error', lines:'Lines', '$':'Cost · USD', s:'Seconds'};
      $$('.stat b', pane).forEach(b => { if (names[b.textContent]) b.textContent = names[b.textContent]; });
      // Retain backend notes (including incomplete line crops) as visible evidence.
    });
  }

  function prepareConsensus(page) {
    const imageCol = page.children[0], reading = page.children[1];
    imageCol.classList.add('source-image'); reading.classList.add('reading-column');
    const matrix = $('.matrix', imageCol);
    if (matrix) {
      const caption = matrix.nextElementSibling;
      const d = disclosure('Reader agreement · full matrix and reliability', caption ? [matrix, caption] : [matrix], 'full-evidence');
      page.append(d);
    }
    const stats = $(':scope > p.mono', imageCol);
    if (stats) {
      const metrics = el('div', 'consensus-metrics');
      for (const [label, pattern, percent] of [
        ['Reader agreement', /agreement ([\d.]+)/, true],
        ['Reference error · norm', /medoid CER norm ([\d.]+)/, false],
        ['Passages to review', /(\d+) on the check-in list/, false],
      ]) {
        const value = stats.textContent.match(pattern)?.[1]; if (value == null) continue;
        const metric = el('div'); metric.append(el('span', '', label), el('strong', '', percent ? `${(Number(value)*100).toFixed(1)}%` : value)); metrics.append(metric);
      }
      stats.className = 'consensus-stats';
      reading.prepend(metrics, disclosure('Starting reader, family gap, and complete scores', [stats]));
    }
    const text = $('.text', reading);
    if (text) {
      const heading = text.previousElementSibling;
      if (heading?.tagName === 'H3') heading.textContent = 'A starting text to review';
      const highlights = el('label', 'highlight-picker', 'Highlight '), select = el('select');
      [['review','Passages needing review'],['all','All disagreements'],['none','Read without highlights']].forEach(([value, label]) => { const o = el('option', '', label); o.value = value; select.append(o); });
      select.setAttribute('aria-label', 'Highlight disagreements'); highlights.append(select);
      text.classList.add('highlight-review');
      select.onchange = () => { text.classList.remove('highlight-review', 'highlight-all', 'highlight-none'); text.classList.add(`highlight-${select.value}`); };
      text.before(highlights, el('p', 'annotation-help', 'Select a marked passage to inspect the alternatives. Agreement measures how similar the readings are; it does not establish correctness.'));
      const detail = el('div', 'annotation-detail'); detail.hidden = true;
      detail.setAttribute('role', 'status'); detail.setAttribute('aria-live', 'polite');
      const close = el('button', '', '×'); close.setAttribute('aria-label', 'Close alternatives');
      const contents = el('div'); detail.append(close, contents); text.after(detail);
      close.onclick = () => { detail.hidden = true; $('mark.selected', text)?.classList.remove('selected'); };
      $$('mark', text).forEach(mark => {
        mark.tabIndex = 0; mark.setAttribute('role', 'button');
        mark.setAttribute('aria-label', `Alternatives for ${mark.textContent || 'an insertion'}`);
        const show = () => {
          $$('mark.selected', text).forEach(m => m.classList.remove('selected'));
          mark.classList.add('selected'); contents.textContent = mark.title.split(' / ').join('\n\n'); detail.hidden = false;
        };
        mark.onclick = show;
        mark.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(); } if (e.key === 'Escape') close.click(); };
      });
    }
    const checks = $(':scope > table', reading);
    if (checks) {
      const heading = checks.previousElementSibling;
      const review = el('div', 'review-list');
      $$('tr', checks).slice(1).forEach(row => {
        const c = [...row.cells]; if (c.length < 5) return;
        const d = disclosure(''); const s = $('summary', d);
        s.append(el('span', 'review-number', `#${c[0].textContent}`), el('span', 'review-base', c[1].textContent || '(insertion)'), el('span', 'review-weight', `${c[3].textContent} readers · weight ${c[2].textContent}`));
        const alternatives = el('div'); alternatives.append(...c[4].childNodes); d.append(alternatives); review.append(d);
      });
      const group = disclosure(`Passages to review · ${review.children.length}`, [el('p', 'muted', heading?.textContent || ''), review]);
      if (heading?.tagName === 'H3') heading.remove(); checks.replaceWith(group);
    }
  }

  function readingWorkspace() {
    makeHeader();
    let pages;
    if (config.kind === 'layout') {
      const section = $('body > section');
      const headings = $$(':scope > h2', section);
      pages = headings.map(h => {
        const article = el('article', 'layout-source'); article.id = h.firstChild.textContent.trim();
        h.before(article); article.append(h);
        while (article.nextSibling && !(article.nextSibling.nodeType === 1 && article.nextSibling.tagName === 'H2')) article.append(article.nextSibling);
        const table = $(':scope > table', article);
        if (table) { const d = disclosure('Region inventory · types, hands, lines, and notes'); table.before(d); d.append(table); }
        const tools = el('div', 'layout-tools'); const label = el('label'); const check = el('input');
        check.type = 'checkbox'; check.checked = true; label.append(check, document.createTextNode(' Show segmentation boxes')); tools.append(label);
        const figures = $('.page', article); figures.before(tools);
        check.onchange = () => $$('svg', article).forEach(svg => svg.hidden = !check.checked);
        return article;
      });
    } else {
      pages = $$('body > section > .page');
      pages.forEach(p => config.kind === 'consensus' ? prepareConsensus(p) : prepareReport(p));
    }
    if (!pages.length) return;
    const shell = el('div', 'review-shell'), nav = el('aside', 'source-nav'), main = el('main', 'review-content');
    main.id = 'review-main'; main.tabIndex = -1;
    nav.setAttribute('aria-label', 'Source navigator');
    nav.append(el('div', 'eyebrow', `${pages.length} source pages`));
    const search = el('input'); search.type = 'search'; search.placeholder = 'Find a source…'; search.setAttribute('aria-label', 'Find a source'); nav.append(search);
    const navigation = el('nav'); navigation.setAttribute('aria-label', 'Choose a source'); nav.append(navigation);
    const bar = el('div', 'source-bar'), sourceTitle = el('div');
    sourceTitle.append(el('div', 'eyebrow', 'Source'), el('h2'), el('span', 'source-kind'));
    const pager = el('div', 'source-pager'); const prev = el('button', '', '←'), next = el('button', '', '→'), counter = el('span', 'source-counter');
    prev.setAttribute('aria-label', 'Previous source'); next.setAttribute('aria-label', 'Next source'); pager.append(prev, counter, next); bar.append(sourceTitle, pager); main.append(bar);
    const navItems = [];
    for (const [synthetic, groupTitle] of [[false, 'Historical sources'], [true, 'Synthetic samples']]) {
      const members = pages.filter(p => /^synth-/.test(p.id) === synthetic); if (!members.length) continue;
      const group = el('div'); group.append(el('div', 'source-group', groupTitle)); navigation.append(group);
      members.forEach(page => {
        const [name, subtitle] = sourceName(page.id); const a = link(name, `#${page.id}`); a.append(el('small', '', subtitle));
        a.title = page.id; a.dataset.source = page.id; group.append(a); navItems.push(a);
      });
    }
    const empty = el('p', 'muted', 'No matching sources.'); empty.hidden = true; navigation.append(empty);
    search.oninput = () => {
      const q = search.value.toLowerCase(); navItems.forEach(a => { a.hidden = !(a.textContent + a.dataset.source).toLowerCase().includes(q); });
      $$(':scope > div', navigation).forEach(g => { g.hidden = !$$('a', g).some(a => !a.hidden); });
      empty.hidden = navItems.some(a => !a.hidden);
    };
    nav.append(el('p', 'nav-foot', 'Historical sources and synthetic samples stay separate. Every reading retains its source and method.'));
    const sections = $$('body > section');
    sections.forEach(section => {
      if (pages.some(p => section.contains(p))) {
        const redundant = $(':scope > h2', section);
        if (redundant?.textContent === 'Every page, every backend') redundant.remove();
        main.append(section);
      } else {
        const d = disclosure('All readers · scores, costs, and run details', [...section.childNodes], 'run-evidence');
        const mixed = pages.some(p => /^synth-/.test(p.id)) && pages.some(p => !/^synth-/.test(p.id));
        if (mixed) $('summary', d).after(el('p', 'muted', 'This original summary averages historical and synthetic pages together. Use the individual source scores to judge performance on real material.'));
        main.append(d); section.remove();
      }
    });
    shell.append(nav, main); document.body.append(shell);
    pages.forEach(page => {
      const originalHeading = config.kind === 'layout' ? $(':scope > h2', page) : $(':scope > div:first-child > h2, :scope > div:first-child > h3', page);
      if (originalHeading) {
        if (config.kind === 'layout') { originalHeading.className = 'mono muted'; originalHeading.style.fontSize = '12px'; }
        else { const d = disclosure('Source identifier', [el('p', 'mono', page.id)], 'provenance'); originalHeading.replaceWith(d); }
      }
      const image = $('.source-image', page);
      if (image) { image.prepend(el('div', 'image-label', 'Original document')); image.append(el('p', 'image-hint', 'Open the image for a closer look ↗')); }
    });
    let active = 0;
    const activate = id => {
      const found = pages.findIndex(p => p.id === id); active = found < 0 ? 0 : found;
      const page = pages[active]; pages.forEach(p => { p.hidden = p !== page; });
      navItems.forEach(a => { if (a.dataset.source === page.id) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
      const [name, sub] = sourceName(page.id); $('h2', sourceTitle).textContent = name; $('.source-kind', sourceTitle).textContent = sub;
      counter.textContent = `${active + 1} / ${pages.length}`; prev.disabled = active === 0; next.disabled = active === pages.length - 1;
    };
    function choose(id) { history.replaceState(null, '', `#${encodeURIComponent(id)}`); activate(id); }
    navItems.forEach(a => a.onclick = e => { e.preventDefault(); choose(a.dataset.source); if (innerWidth < 801) bar.scrollIntoView({block:'start'}); });
    prev.onclick = () => choose(pages[active - 1].id); next.onclick = () => choose(pages[active + 1].id);
    const fromHash = () => { let id = ''; try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) {} activate(id); };
    window.addEventListener('hashchange', fromHash); fromHash();
  }

  function home() {
    const main = $('body > main'); main.id = 'review-main';
    const h1 = $('h1', main), sub = $('.sub', main), legend = $('.legend', main);
    const hero = el('header', 'collection-hero'), words = el('div');
    words.append(el('div', 'eyebrow', 'A research collection / November 2026'), h1, sub);
    const actions = el('div', 'collection-links'); actions.append(link('Explore transcription ↓', '#transcription'), link('Explore maps ↓', '#maps')); words.append(actions);
    const figure = el('figure', 'hero-image'); const img = el('img'); img.src = '01-use-cases/transcription/01-fraktur-print-bakeoff/inputs/pages/real-grimm-khm-1812-i-p093.jpg'; img.alt = 'A page of Grimm’s fairy tales, printed in Fraktur in 1812';
    figure.append(img, el('figcaption', '', 'GRIMM · 1812 · A SOURCE IN THIS COLLECTION')); hero.append(words, figure); main.prepend(hero);
    const headers = $$(':scope > h2', main);
    const descriptions = [
      'Compare nine readers on printed sources, then inspect the passages where their readings diverge.',
      'Follow the same comparison through letters and an album, from a clear hand to difficult photographs.',
      'See how readers divide a page into regions and lines before they transcribe it.',
      'Follow 24 historical place names from a ledger to a map, with the reason for every match.',
      'Inspect the historical map search and the evidence behind the decision to leave the overlay off.',
      'Trace a map point all the way back to the page and line where its name appeared.',
      'Explore place-name histories around Breslau and the changes recorded across 1945.',
    ];
    let grid, count = 0;
    headers.forEach(h => {
      const section = el('section'); h.before(section); section.append(h);
      while (section.nextSibling && !(section.nextSibling.nodeType === 1 && section.nextSibling.tagName === 'H2')) section.append(section.nextSibling);
      const flow = $('.flow', section), output = flow && $('.out', flow);
      const isCase = /^(Transcription|Maps) ·/.test(h.textContent);
      if (isCase) {
        const isText = h.textContent.startsWith('Transcription');
        if (count === 0 || count === 3) {
          const intro = el('div', 'collection-intro'); intro.id = isText ? 'transcription' : 'maps';
          intro.append(el('div', 'eyebrow', isText ? '01 / Read the sources' : '02 / Locate the places'), el('h2', '', isText ? 'Transcription & review' : 'Maps & place histories'));
          section.before(intro); grid = el('div', 'collection-grid'); section.before(grid);
        }
        section.className = 'case-card'; grid.append(section);
        h.textContent = h.textContent.split(' · ').slice(1).join(' · ');
        section.prepend(el('div', 'eyebrow', `Experiment ${String(count + 1).padStart(2, '0')}`));
        h.after(el('p', 'case-desc', descriptions[count]));
        const actions = el('div', 'case-actions');
        if (output) $$('a', output).forEach(a => { const copy = a.cloneNode(true); if (copy.textContent === 'Explorer') copy.textContent = 'Compare readers ↗'; if (copy.textContent === 'Consensus') copy.textContent = 'Review disagreements ↗'; if (copy.textContent === 'Map') copy.textContent = 'Explore map ↗'; actions.append(copy); });
        const result = $(':scope > p.num', section); if (result) result.classList.add('case-result');
        section.append(actions);
        if (flow) { const d = disclosure('How this experiment works', [flow]); section.append(d); }
        count++;
      } else {
        section.className = 'collection-notes';
        if (h.textContent === 'The shape of the work') {
          const d = disclosure('The complete workflow · from page to map', [...section.childNodes]); if (legend) d.append(legend); section.append(d);
        }
        if (h.textContent === 'Where the evidence is') { const table = $('table', section); if (table) section.append(disclosure('Find the files behind a result', [table])); }
      }
    });
  }

  function maps() {
    const main = $('body > main'); main.id = 'review-main';
    const controls = $('.controls');
    const advanced = disclosure('Map options'); const options = el('div'); advanced.append(options);
    ['allmaps', 'overlayOpacity', 'theme'].forEach(id => { const input = document.getElementById(id); if (input) options.append(input.closest('label')); });
    const legend = $('.legend', controls); if (legend) options.append(legend);
    controls.append(advanced);
    $('#yearMin').setAttribute('aria-label', 'Start year'); $('#yearMax').setAttribute('aria-label', 'End year');
    const aside = $('aside', main), unresolved = $('#unresolvedList');
    if (unresolved) {
      const explanation = unresolved.previousElementSibling, heading = explanation?.previousElementSibling;
      const d = disclosure(`Unresolved names · ${unresolved.children.length}`);
      if (heading?.tagName === 'H2') heading.remove();
      if (explanation) d.append(explanation); d.append(unresolved); aside.append(d);
    }
    const detail = $('#detail');
    if (detail) {
      const groupEvidence = () => {
        if ($('.cand', detail) && !$('.candidate-disclosure', detail)) {
          $$(':scope > h3', detail).filter(h => h.textContent.startsWith('Gazetteer candidates')).forEach(h => {
            const d = disclosure(h.textContent, [], 'candidate-disclosure'); h.before(d); h.remove();
            while (d.nextElementSibling && d.nextElementSibling.tagName !== 'H3') d.append(d.nextElementSibling);
          });
        }
        $$('table', detail).forEach(wrapTable);
      };
      new MutationObserver(groupEvidence).observe(detail, {childList:true});
    }
    // Existing MapLibre listeners remain attached to the original controls.
    advanced.addEventListener('toggle', () => window.dispatchEvent(new Event('resize')));
    window.dispatchEvent(new Event('resize'));
  }

  if (config.kind === 'home') home();
  else if (config.kind === 'map') maps();
  else readingWorkspace();
  $$('table').forEach(wrapTable);
})();
