// Run with: node --test tests/timeline_state.test.cjs
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const source = readFileSync(new URL('../src/mueser/timeline/web/timeline.js', `file://${__filename}`), 'utf8');
const end = source.indexOf('  // ------------------------------------------------------------------ render');
assert.ok(end > 0);
function harness(log = [], edges = []) {
  const data = { nodes: [{ id: 'Q1', type: 'person' }, { id: 'C1', type: 'concept' }], edges, log };
  const context = vm.createContext({
    document: { getElementById: () => ({ textContent: JSON.stringify(data) }) },
    location: { pathname: '/synthetic-case/outputs/index.html' },
  });
  vm.runInContext(source.slice(0, end) + 'globalThis.qa = { store, state, edgesOf, classCounts };})();', context);
  return context.qa;
}
const added = { id: 'synthetic-added-edge', type: 'edge', who: 'QA', body: { src: 'Q1', dst: 'C1', type: 'influenced_by' } };
test('a new connection class is visible immediately and included in layer counts', () => {
  const qa = harness();
  qa.store.local.push(added);
  assert.equal(qa.edgesOf('Q1').length, 1);
  assert.equal(qa.classCounts()['person–concept'], 1);
  qa.state.layers.delete('person–concept');
  assert.equal(qa.edgesOf('Q1').length, 0);
});
test('a connection restored from the embedded log remains visible without a database rebuild', () => {
  const qa = harness([added]);
  assert.equal(qa.edgesOf('Q1')[0].dst, 'C1');
  assert.equal(qa.classCounts()['person–concept'], 1);
});
