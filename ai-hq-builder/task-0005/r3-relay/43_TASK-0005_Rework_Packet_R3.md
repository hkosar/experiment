# 43 — TASK-0005 Rework Packet R3 (APP-07): P2X Authority-Binding Corrections

**Task:** TASK-0005, rework cycle R3. **Instruction authority:** `34_` + `37_` + `40_` + this packet; **governing findings `41_`/`41A_` — INCLUDED IN THIS RELAY ZIP**; dispositions `42_` (included). All standing rules carry forward; allowlist unchanged (`design/traces/behavioral/**` + `13V_validate_design_matrix.py`); returns to Fable; one-zip transport.

## Findings to correct (defeat every `41A_` probe in exact form, in shipped evidence)

- **RW-37 (P2X-01):** the manifest binds the receipt registry's **content digest** (same algorithm/length discipline as the envelope), not its label; the two-registries-one-label probe ships failing both ways.
- **RW-38 (P2X-02):** receipts carry a purpose matched against the consuming action/evidence contract (a display receipt can never ground a consequential action) and identity fields (authority id + version) agreeing exactly with the owning registry; both probes ship failing.
- **RW-39 (P2X-03):** `expected_current_version` is **mandatory** on every change to an existing schedule — omission is a usage error, never a default-pass; the omit-probe ships failing.
- **RW-40 (P2X-04):** run receipts name the exact schedule version / activation epoch; the watchdog matches deadline satisfaction per-version — a stale-version receipt never satisfies a newer version's deadline; the stale-scheduler probe ships failing-then-detected.
- **RW-41 (P2X-05):** journal replay validates transition invariants before producing any state: duplicate definitions, contradictory recurrences, orphaned references, gaps, and out-of-order version events all REFUSE replay with a named reason; the contradictory-history probe ships failing; a well-formed journal still replays deterministically (positive case).

## Return requirements
Per-finding disposition with shipped-evidence proof; every `41A_` probe defeated in exact form; all standing criteria re-proven; APP-06 record with reflexive falsifiers; **one zip, returned to Fable**.
