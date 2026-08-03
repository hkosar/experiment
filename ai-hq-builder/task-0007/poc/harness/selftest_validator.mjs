/**
 * Self-test for validate_n8n_workflows.mjs.
 *
 * Each case is a deliberately broken workflow that must be REJECTED, plus one
 * well-formed control that must be ACCEPTED. A validator whose failure path has
 * never executed is not evidence, so its failure path executes here.
 */
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const VALIDATOR = join(HERE, 'validate_n8n_workflows.mjs');

const good = {
  name: 'control',
  nodes: [
    { parameters: {}, id: 'a', name: 'A Trigger', type: 'n8n-nodes-base.scheduleTrigger', typeVersion: 1, position: [0, 0] },
    { parameters: {}, id: 'b', name: 'B', type: 'n8n-nodes-base.noOp', typeVersion: 1, position: [200, 0] },
  ],
  connections: { 'A Trigger': { main: [[{ node: 'B', type: 'main', index: 0 }]] } },
};

const clone = (o) => JSON.parse(JSON.stringify(o));

const cases = [
  ['well-formed control', good, true],
  ['malformed JSON', '{ not json', false],
  ['no trigger', (() => { const w = clone(good); w.nodes[0].type = 'n8n-nodes-base.noOp'; w.nodes[0].name = 'A'; w.connections = { A: { main: [[{ node: 'B', type: 'main', index: 0 }]] } }; return w; })(), false],
  ['duplicate node names', (() => { const w = clone(good); w.nodes[1].name = 'A Trigger'; w.connections = {}; return w; })(), false],
  ['duplicate node ids', (() => { const w = clone(good); w.nodes[1].id = 'a'; return w; })(), false],
  ['connection to a nonexistent node', (() => { const w = clone(good); w.connections['A Trigger'].main[0][0].node = 'Ghost'; return w; })(), false],
  ['connection from a nonexistent node', (() => { const w = clone(good); w.connections.Ghost = { main: [[{ node: 'B', type: 'main', index: 0 }]] }; return w; })(), false],
  ['orphaned node', (() => { const w = clone(good); w.connections = {}; return w; })(), false],
  ['node missing a required field', (() => { const w = clone(good); delete w.nodes[1].typeVersion; return w; })(), false],
  ['malformed position', (() => { const w = clone(good); w.nodes[1].position = [5]; return w; })(), false],
];

let pass = 0;
const rows = [];
for (const [label, body, shouldAccept] of cases) {
  const dir = mkdtempSync(join(tmpdir(), 'wfcase-'));
  writeFileSync(join(dir, 'case.json'), typeof body === 'string' ? body : JSON.stringify(body));
  let accepted;
  try {
    execFileSync(process.execPath, [VALIDATOR], { env: { ...process.env, POC_WF_DIR: dir }, stdio: 'pipe' });
    accepted = true;
  } catch { accepted = false; }
  rmSync(dir, { recursive: true, force: true });
  const ok = accepted === shouldAccept;
  if (ok) pass++;
  rows.push({ case: label, expected: shouldAccept ? 'accept' : 'reject', actual: accepted ? 'accept' : 'reject', ok });
  process.stderr.write(`  [${ok ? 'ok  ' : 'FAIL'}] ${label} — expected ${shouldAccept ? 'accept' : 'reject'}, got ${accepted ? 'accept' : 'reject'}\n`);
}
console.log(JSON.stringify({ check: 'validator self-test', cases: rows, passed: pass, total: cases.length }, null, 2));
process.stderr.write(pass === cases.length ? `VALIDATOR SELF-TEST PASS — ${pass} cases\n` : `VALIDATOR SELF-TEST FAIL — ${pass}/${cases.length}\n`);
process.exit(pass === cases.length ? 0 : 1);
