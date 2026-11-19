// Run with: node --test tests/timeline_queue.test.cjs
// Exercise the production store with synthetic storage and HTTP responses; no real logs.
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const source = readFileSync(new URL('../src/mueser/timeline/web/timeline.js', `file://${__filename}`), 'utf8');
const start = source.indexOf('  const KEY =');
const end = source.indexOf('\n  function ts()', start);
assert.ok(start >= 0 && end > start);
const event = { id: 'synthetic-note', type: 'question', body: { text: 'Test only' } };
const reply = (data, ok = true) => ({ ok, status: ok ? 200 : 503, json: async () => data });
function harness(fetch, memory = new Map(), dataId = 'synthetic-build') {
  const context = vm.createContext({
    fetch, state: { online: true, serverEvents: 0 }, D: { log: [], data_id: dataId },
    location: { pathname: '/synthetic-case/outputs/index.html' },
    localStorage: { getItem: k => memory.get(k), setItem: (k, v) => memory.set(k, v) },
    toast() {}, renderConn() {},
  });
  vm.runInContext(source.slice(start, end) + '\nglobalThis.store = store;', context);
  return { store: context.store, state: context.state, memory };
}
test('reload during an in-flight save preserves a retryable event', async () => {
  let finish;
  const first = harness(() => new Promise(resolve => { finish = resolve; }));
  const saving = first.store.add(event);
  const reload = harness(async () => reply({ ok: true, id: event.id }), first.memory);
  reload.store.load();
  assert.equal(reload.store.pending.has(event.id), true);
  await reload.store.flush();
  assert.equal(reload.store.pending.size, 0);
  finish(reply({ ok: true, id: event.id, duplicate: true }));
  await saving;
});
test('a temporary rejected save is retried while ping remains healthy', async () => {
  let writes = 0;
  const { store, state } = harness(async path => path === '/api/ping'
    ? reply({ data_id: 'synthetic', events: 0 })
    : ++writes === 1 ? reply({ error: 'temporary failure' }, false) : reply({ ok: true, id: event.id }));
  assert.equal(await store.add(event), false);
  assert.equal(state.online, true);
  await store.reconnect();
  assert.equal(writes, 2);
  assert.equal(store.pending.size, 0);
});
test('another application on the same origin cannot acknowledge timeline events', async () => {
  const { store, state } = harness(async () => reply({ build_id: 'reading-room', events: 0 }));
  assert.equal(await store.ping(), false);
  assert.equal(state.online, false);
});
test('a successful HTTP response needs an event acknowledgement', async () => {
  const { store } = harness(async () => reply({ ok: true, id: 'wrong-event' }));
  assert.equal(await store.add(event), false);
  assert.equal(store.pending.has(event.id), true);
});
test('duplicate acknowledgements do not inflate the saved event count', async () => {
  const { store, state } = harness(async () => reply({ ok: true, id: event.id, duplicate: true }));
  assert.equal(await store.add(event), true);
  assert.equal(state.serverEvents, 0);
});
test('unavailable browser storage is surfaced while keeping the event exportable', async () => {
  const { store, state } = harness(async () => { throw Error('offline'); }, { set() { throw Error('quota'); } });
  state.online = false;
  assert.equal(await store.add(event), false);
  assert.equal(store.durable, false);
  assert.equal(store.local[0].id, event.id);
});
test('unsent notes survive rebuilding the case with a new data id', async () => {
  const first = harness(async () => { throw Error('offline'); });
  await first.store.add(event);
  const rebuilt = harness(async () => reply({ ok: true, id: event.id }), first.memory, 'next-build');
  rebuilt.store.load();
  assert.equal(rebuilt.store.pending.has(event.id), true);
  await rebuilt.store.flush();
  assert.equal(rebuilt.store.pending.size, 0);
});
test('the existing build-specific queue is retained on first upgrade', () => {
  const memory = new Map([['mueser.timeline.synthetic-build', JSON.stringify({ events: [event], pending: [event.id] })]]);
  const { store } = harness(async () => {}, memory);
  store.load();
  assert.equal(store.pending.has(event.id), true);
  assert.equal(store.local[0].id, event.id);
});
