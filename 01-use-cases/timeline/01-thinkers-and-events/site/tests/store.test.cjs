// Exercise the actual Store callbacks and effects with deterministic hooks, storage and HTTP.
// No browser or real log is modified. Run: node --test tests/*.test.cjs (from site/).
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const ts = require('typescript');
const source = ts.transpileModule(readFileSync(require.resolve('../components/Store.tsx'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
}).outputText;
const reply = (body, ok = true) => ({ ok, status: ok ? 200 : 503, json: async () => body });
const event = id => ({ id, ts: '2026-11-19T12:00:00Z', type: 'comment', body: { text: 'Synthetic QA only' } });
const key = 'mueser.timeline.site.synthetic-case';

function harness(fetch, memory = new Map(), dataId = 'build-one') {
  const slots = [], effects = [], intervals = new Set();
  let cursor = 0, dirty = true, value;
  const same = (a, b) => a && b && a.length === b.length && a.every((v, i) => Object.is(v, b[i]));
  const memo = (fn, deps) => {
    const i = cursor++;
    if (!slots[i] || !same(slots[i].deps, deps)) slots[i] = { value: fn(), deps };
    return slots[i].value;
  };
  const hooks = {
    createContext: () => ({ Provider: 'provider' }),
    useState(initial) {
      const i = cursor++;
      if (!(i in slots)) slots[i] = typeof initial === 'function' ? initial() : initial;
      return [slots[i], v => { const next = typeof v === 'function' ? v(slots[i]) : v; if (!Object.is(next, slots[i])) { slots[i] = next; dirty = true; } }];
    },
    useRef: value => memo(() => ({ current: value }), []),
    useCallback: (fn, deps) => memo(() => fn, deps), useMemo: memo,
    useEffect(fn, deps) {
      const i = cursor++;
      if (!slots[i] || !same(slots[i].deps, deps)) {
        const prev = slots[i]; slots[i] = { deps };
        effects.push(() => { prev?.cleanup?.(); slots[i].cleanup = fn(); });
      }
    },
  };
  const context = vm.createContext({
    exports: {}, fetch, Date, Math, Set, Promise, console,
    require: name => name === 'react' ? hooks : name === 'react/jsx-runtime'
      ? { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }) }
      : (() => { throw Error(name); })(),
    localStorage: { getItem: k => memory.get(k) ?? null, setItem: (k, v) => memory.set(k, v) },
    setTimeout: () => 1, clearTimeout() {}, setInterval: fn => { intervals.add(fn); return fn; }, clearInterval: fn => intervals.delete(fn),
  });
  vm.runInContext(source, context);
  const meta = { case_id: 'synthetic-case', data_id: dataId, classes: {}, class_names: { 'person–concept': 'Thinkers to concepts' }, edge_types: {}, nodes: 0, edges: 0, model: null };
  function render() {
    for (let n = 0; dirty && n < 20; n++) {
      dirty = false; cursor = 0;
      value = context.exports.Store({ meta, children: null }).props.value;
      while (effects.length) effects.shift()();
    }
  }
  async function settle() { for (let i = 0; i < 12; i++) { await new Promise(resolve => setImmediate(resolve)); render(); } }
  render();
  return { get value() { render(); return value; }, memory, settle, async tick() { for (const fn of [...intervals]) await fn(); await settle(); } };
}
const ping = () => reply({ case_id: 'synthetic-case', data_id: 'build-one', events: 0 });

test('a reader can see connections of a class absent from the built dataset', async () => {
  const h = harness(async () => ping()); await h.settle();
  assert.equal(h.value.layers.has('person–concept'), true);
  h.value.toggleLayer('person–concept');
  assert.equal(h.value.layers.has('person–concept'), false);
  h.value.allOn(); assert.equal(h.value.layers.has('person–concept'), true);
});

test('a note created offline is retried by the existing reconnect timer', async () => {
  let online = false, writes = 0;
  const h = harness(async (url, opts) => {
    if (!online) throw Error('offline');
    if (url === '/api/ping') return ping();
    writes++; return reply({ ok: true, id: JSON.parse(opts.body).id });
  });
  await h.settle();
  await h.value.add(event('offline-note'));
  online = true; await h.tick();
  assert.equal(writes, 1);
  assert.equal(h.value.pending, 0);
});

test('an acknowledgement cannot erase a newer note added while the first save is in flight', async () => {
  let release, writes = 0;
  const h = harness(async (url, opts) => {
    if (url === '/api/ping') return ping();
    if (++writes === 1) return new Promise(resolve => { release = () => resolve(reply({ ok: true, id: JSON.parse(opts.body).id })); });
    return reply({ error: 'temporary failure' }, false);
  });
  await h.settle();
  const first = h.value.add(event('first'));
  const second = h.value.add(event('second'));
  release(); await Promise.all([first, second]); await h.settle();
  assert.deepEqual(Array.from(h.value.unsent, e => e.id), ['second']);
  assert.deepEqual(JSON.parse(h.memory.get(key)).unsent.map(e => e.id), ['second']);
});

test('pending notes survive a dataset rebuild and are retried after reload', async () => {
  const first = harness(async () => { throw Error('offline'); });
  await first.settle(); await first.value.add(event('rebuild-note'));
  let writes = 0;
  const next = harness(async (url, opts) => {
    if (url === '/api/ping') return ping();
    writes++; return reply({ ok: true, id: JSON.parse(opts.body).id });
  }, first.memory, 'build-two');
  await next.settle();
  assert.equal(writes, 1); assert.equal(next.value.pending, 0);
});

test('the old build-specific queue is migrated and a false acknowledgement keeps the event pending', async () => {
  const memory = new Map([['mueser.timeline.site.build-one', JSON.stringify({ unsent: [event('legacy')] })]]);
  const h = harness(async url => url === '/api/ping' ? ping() : reply({ ok: true, id: 'wrong' }), memory);
  await h.settle();
  assert.equal(h.value.pending, 1);
  assert.equal(JSON.parse(memory.get(key)).unsent[0].id, 'legacy');
});

test('healthy pings retry a failed save without requiring a connection change', async () => {
  let works = false;
  const h = harness(async (url, opts) => url === '/api/ping' ? ping() : works
    ? reply({ ok: true, id: JSON.parse(opts.body).id }) : reply({ error: 'retry later' }, false));
  await h.settle(); await h.value.add(event('retry')); works = true; await h.tick();
  assert.equal(h.value.pending, 0);
});

test('a different case on the same origin cannot receive a queued note', async () => {
  let writes = 0;
  const h = harness(async url => {
    if (url === '/api/ping') return reply({ case_id: 'different-case', data_id: 'other', events: 0 });
    writes++; return reply({ ok: true, id: 'note' });
  });
  await h.settle(); await h.value.add(event('note')); await h.tick();
  assert.equal(writes, 0); assert.equal(h.value.pending, 1);
});
