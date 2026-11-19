const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const ts = require('typescript');
const context = vm.createContext({ exports: {}, require, process });
vm.runInContext(ts.transpileModule(readFileSync(require.resolve('../lib/log.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
}).outputText, context);
const { validate } = context.exports;
const base = { id: 'synthetic', ts: '2026-11-19T12:00:00Z', type: 'comment', body: { text: 'Test only' } };

test('rejects field types that would make the shared Python log unreadable', () => {
  const invalid = [
    { who: {} }, { who: null }, { client: 42 }, { data_id: [] }, { ref: 3 },
    { body: [] }, { body: null }, { anchor: [] }, { anchor: { node: 42 } },
    { anchor: { edge: {} } }, { anchor: { field: [] } }, { anchor: { quote: null } },
  ];
  for (const fields of invalid) assert.ok(validate({ ...base, ...fields }), JSON.stringify(fields));
});

test('edge endpoints and relation names must be nonempty strings', () => {
  for (const value of [{}, [], 42, true, '']) {
    for (const field of ['src', 'dst', 'type']) {
      assert.ok(validate({ ...base, type: 'edge', body: { src: 'Q1', dst: 'Q2', type: 'influenced_by', [field]: value } }));
    }
  }
});

test('valid events for each interaction remain readable by the Python model', () => {
  const events = [base,
    { ...base, type: 'question', anchor: { node: 'Q1', quote: 'An excerpt' } },
    { ...base, type: 'issue', who: 'Synthetic QA', client: 'timeline-site', data_id: 'test-build' },
    { ...base, type: 'decision', anchor: { edge: 'edge-id' }, body: { choice: 'accept' } },
    { ...base, type: 'edge', body: { src: 'Q1', dst: 'Q2', type: 'influenced_by' } },
    { ...base, type: 'status', ref: 'issue-id', body: { status: 'resolved' } },
    { ...base, type: 'excerpt', anchor: null, data_id: null, ref: null },
  ];
  for (const e of events) assert.equal(validate(e), null);
  const root = path.resolve(__dirname, '../../../../..');
  const result = spawnSync(path.join(root, '.venv/bin/python'), ['-c',
    'import json,sys; from mueser.timeline.log import Event; [Event.model_validate(e) for e in json.load(sys.stdin)]'],
    { cwd: root, input: JSON.stringify(events), encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr || String(result.error));
});
