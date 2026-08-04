/**
 * Structural validation of the POC n8n workflow definitions.
 *
 * WHAT THIS PROVES: the JSON parses, constructs as a real `n8n-workflow`
 * Workflow object, has unique node names/ids, has a trigger, and every
 * connection references a node that exists with a reachable graph.
 *
 * WHAT THIS DOES NOT PROVE — stated because the packet's §4 partial-mechanism
 * rule applies to the Builder too: it does NOT validate node types or their
 * parameters. That needs `n8n-nodes-base`, whose install is blocked by this
 * environment's egress proxy (403). Parameter correctness is therefore
 * NOT TESTED here and is settled at import time in the owner session, which
 * is step 6 of RUNBOOK-n8n.md.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

// n8n-workflow's ESM build uses extensionless relative imports, which Node's
// ESM resolver refuses. Load its CommonJS entry point instead — same library,
// same version, and it is the build n8n itself ships to Node consumers.
const require = createRequire(import.meta.url);
const { Workflow } = require('n8n-workflow');

const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = process.env.POC_WF_DIR || join(HERE, '..', 'workflows', 'n8n');

// A stub registry: we have no node types, and we say so rather than pretend.
const stubNodeTypes = {
  getByName: () => undefined,
  getByNameAndVersion: () => undefined,
  getKnownTypes: () => ({}),
};

const results = [];
let failures = 0;

for (const file of readdirSync(DIR).filter((f) => f.endsWith('.json')).sort()) {
  const problems = [];
  const raw = readFileSync(join(DIR, file), 'utf8');
  let wf;
  try {
    wf = JSON.parse(raw);
  } catch (e) {
    results.push({ file, ok: false, problems: [`JSON parse failed: ${e.message}`] });
    failures++;
    continue;
  }

  const names = wf.nodes.map((n) => n.name);
  const ids = wf.nodes.map((n) => n.id);
  const dupNames = names.filter((n, i) => names.indexOf(n) !== i);
  const dupIds = ids.filter((n, i) => ids.indexOf(n) !== i);
  if (dupNames.length) problems.push(`duplicate node names: ${[...new Set(dupNames)].join(', ')}`);
  if (dupIds.length) problems.push(`duplicate node ids: ${[...new Set(dupIds)].join(', ')}`);

  for (const n of wf.nodes) {
    for (const field of ['name', 'type', 'typeVersion', 'position']) {
      if (n[field] === undefined) problems.push(`node ${n.name ?? '(unnamed)'} missing ${field}`);
    }
    if (!Array.isArray(n.position) || n.position.length !== 2) {
      problems.push(`node ${n.name} has a malformed position`);
    }
  }

  // Every connection endpoint must resolve to a real node, both sides.
  const nameSet = new Set(names);
  for (const [from, conn] of Object.entries(wf.connections ?? {})) {
    if (!nameSet.has(from)) problems.push(`connection source ${from} is not a node`);
    for (const outputs of Object.values(conn)) {
      for (const branch of outputs) {
        for (const target of branch ?? []) {
          if (!nameSet.has(target.node)) {
            problems.push(`connection ${from} -> ${target.node}: target is not a node`);
          }
        }
      }
    }
  }

  // A workflow with no trigger can never start. Detected by name convention on
  // the type string, which is all we can do without the node-type registry.
  const triggers = wf.nodes.filter(
    (n) => /trigger$/i.test(n.type) || n.type.endsWith('.webhook'),
  );
  if (!triggers.length) problems.push('no trigger or webhook node — the workflow cannot start');

  // Reachability from the trigger(s): an orphaned node is usually a wiring slip.
  const adj = new Map();
  for (const [from, conn] of Object.entries(wf.connections ?? {})) {
    const outs = [];
    for (const outputs of Object.values(conn)) {
      for (const branch of outputs) for (const t of branch ?? []) outs.push(t.node);
    }
    adj.set(from, outs);
  }
  const seen = new Set(triggers.map((t) => t.name));
  const stack = [...seen];
  while (stack.length) {
    for (const nxt of adj.get(stack.pop()) ?? []) {
      if (!seen.has(nxt)) { seen.add(nxt); stack.push(nxt); }
    }
  }
  const orphans = names.filter((n) => !seen.has(n));
  if (orphans.length) problems.push(`unreachable from any trigger: ${orphans.join(', ')}`);

  // Construct the real Workflow object — this is the library's own acceptance.
  try {
    // eslint-disable-next-line no-new
    new Workflow({
      id: wf.meta?.poc ?? file,
      name: wf.name,
      nodes: wf.nodes,
      connections: wf.connections ?? {},
      active: false,
      nodeTypes: stubNodeTypes,
      settings: wf.settings ?? {},
    });
  } catch (e) {
    problems.push(`n8n-workflow rejected the definition: ${e.message}`);
  }

  if (problems.length) failures++;
  results.push({
    file,
    ok: problems.length === 0,
    nodes: wf.nodes.length,
    triggers: triggers.map((t) => t.name),
    connections: Object.keys(wf.connections ?? {}).length,
    problems,
  });
}

const report = {
  check: 'n8n workflow structural validation',
  library: 'n8n-workflow',
  node_type_registry_available: false,
  node_types_and_parameters: 'NOT TESTED — n8n-nodes-base blocked by egress proxy (403)',
  workflows: results,
  all_ok: failures === 0,
};
console.log(JSON.stringify(report, null, 2));
for (const r of results) {
  const mark = r.ok ? 'PASS' : 'FAIL';
  process.stderr.write(`  [${mark}] ${r.file}  ${r.nodes} nodes, trigger(s): ${r.triggers?.join(', ')}\n`);
  for (const p of r.problems ?? []) process.stderr.write(`         - ${p}\n`);
}
process.stderr.write(
  failures === 0
    ? 'STRUCTURAL VALIDATION PASS (node types and parameters NOT TESTED)\n'
    : `STRUCTURAL VALIDATION FAIL — ${failures} workflow(s)\n`,
);
process.exit(failures === 0 ? 0 : 1);
