# 34 — TASK-0005 Task Packet: P2U Executable Corrections

**Task:** TASK-0005 (allocated trail entry 102; parent TOPIC-0002; Builder Claude Opus 5). **Instruction authority:** this packet; governing findings `32_`/`32A_` (the verifier's exact required-correction texts govern); dispositions `33_`. All standing TASK-0003/0004 binding rules carry forward unchanged (anti-circularity, determinism, hygiene, shipped-evidence-only claims, no orphaned switches, no dead mutations, record-vs-file re-check, fixture corpus frozen, scope-deviation ⇒ change request).

## Work items (each must defeat the corresponding `32A_` probes in shipped evidence)

- **W1 (P2U-01):** presentation expectations either genuinely compared (compute the requested surface; corruptions like "completely wrong card" must FAIL) or truthfully reclassified outside-simulator — the "mapped" count may not include any expectation lacking a comparator; per-dimension accounting restated.
- **W2 (P2U-02):** `external_basis` resolver contract — every declared reference must resolve against an enumerable registry of externally-owned records present in the fold input, else the case fails closed; the four `store:definitely-missing` probes ship as failing cases; a resolvable-reference positive case ships too.
- **W3 (P2U-03):** version-bound schedule horizons — prior-version horizon coverage becomes ineligible at the atomic change; the verifier's exact probe ships (v1 horizon materialized → v2 change → scheduler death ⇒ v2 liveness warning fires; stale v1 coverage cannot suppress it).
- **W4 (P2U-05):** `13V_ --final-gate` fails globally on ANY open `blocks_gate: true` finding and on a missing/unreadable/malformed `13F_`, independent of row dependencies (rows remain traceability); the verifier's cleared-rows and deleted-file probes become failing self-test cases.

## Allowlist
`design/traces/behavioral/**` (modify+new) · `13V_validate_design_matrix.py` (extend). Nothing else — no documents, no fixtures, no gate artifacts, no `13F_` (Fable-maintained), no checker (unless a W-item strictly requires it; if so, return a change request first).

## Acceptance criteria
(1) All standing criteria re-pass (determinism two-run byte-identical; anti-circularity; hygiene; allowlist walk). (2) Every `32A_` probe reproduced and defeated in shipped output. (3) Per-item disposition table with shipped-evidence proof. (4) No regressions except where a W-item legitimately changes behavior — each individually dispositioned. (5) APP-06 Delivery Record with reflexive falsifiers. Return as zip + RETURN_MANIFEST + record; fingerprint quoted in-channel. Failure clause: APP-07 rework from Fable.
