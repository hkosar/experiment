# Builder Delivery Record — TASK-0003 (closure micro-return, C1)

**Task:** TASK-0003 — P2S-01 Behavioral Candidate-Transition/Fold Simulator (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §7).
**Instruction authority:** `22_` Task Packet + `23_` R1 + `24_` R2 + `25_` R3 + `26_` R4 + `27_` CR answer & errata.
**Status:** **Closure return delivered; independent re-verification pending.** No design-gate passage, P2S-01 closure, or record-shape selection is claimed — that remains Fable's to declare.

---

## 1. The hub ruling, applied

`27_` answered the change request: the quotation was partial, but not in a way that
adds a band. **`hub` is not a band.** D-B7 ATT-03 defines a hub update as the
Record-only band **plus a hub-visibility presentation flag**.

| Change | Where | Effect |
| --- | --- | --- |
| Fifth band **deleted**. Vocabulary is exactly the four §2.1 bands. | `engine_core.py` `ATTENTION_ORDER` | Critical / Needs-Owner / Briefing / Record-only. |
| `hub_visibility` added as a **flag** on `BaseDisposition` and `ComputedResult`, threaded through every stage that rebuilds a disposition. | `engine_core.py`, `simulate.py` | ATT-03's decomposition, not a band. |
| **A14** — the SCH-02 expired path emitted Needs-Owner. Corrected to Record-only + hub-visibility. | `engine_core.py` | The refusal is a background outcome with no owner in the loop (`instruction_authority: none (standing rules govern)`); §2.1 defines Needs-Owner as *"queue admission, next natural session"* and nothing is queued — the same defect class as R4's S9. |
| **S7** — the spoof branch emitted the deleted band. Corrected to Briefing, ceiling unchanged at record-only. | `engine_core.py` | A spoofed message inside a triage batch is classified and summarised with the other five: §2.1 Briefing = *"scheduled digest"*. ATT-03's hub mapping is **not** claimed here — a spoof detection is not a background completion. |
| Queue-admission threshold was the deleted band's order index. | `simulate.py` | Now `>= Needs-Owner`, which is the band §2.1 itself defines as *"queue admission"*. Better grounded than the index it replaced. |
| `pc7`'s `attention_min="hub"` | `run_composition.py` | Now a real band; same conjunction mechanism, still discriminating. |
| Oracle mapping: `"Hub"` → **equality on band AND flag**, not the ceiling used for a bare "None". | `oracle.py`, `judge.py` | Per answer 2. |

**Result: S7 and A14's 6 combinations move from UNRESOLVED to compared, and both
pass.** Attention coverage is now **22/27 fixtures (66/81 combinations)**, 5 unmapped,
**0 unresolved**.

**Exactly 6 combinations changed** — S7 and A14 across three shapes. Every other
computed field on the other 75 is byte-identical to the R4 return. Neither change
needed the diagnosis escalation `27_` allowed for: S7's batch semantics resolved
cleanly once the band vocabulary was right, so no further change request arises.

**Falsifiability of the flag, not just the band:** new `hub-visibility-lost` mutation,
witnessing `expected_attention` at `A14/S1,S2,S3` in the shipped layer-D output. The
band alone could not witness the flag's leg of the comparison.

**One trigger-scope note, stated rather than buried.** ATT-03's enumerated trigger is
*"verified successful background completion"*, and A14 is a **refused** run. `27_`
adjudicates A14's expectation as Record-only + flag directly, so I applied the
mapping's shape to an adjacent trigger and said so at the code site. If ATT-03's
trigger list is meant to be exhaustive, that is a change request, not a defect.

**ATT-03's other mappings are declared, not coded**, per the instruction: safe
automatic retry → Briefing, first overdue reminder → Briefing, subsequent overdue
steps per the B10 aging ladder. No fixture exercises any of them.

**One deliberate naming choice, so it can be overruled.** The engine keeps `none` as
the identifier for D-B7's Record-only band rather than renaming it `record-only`,
because that string is byte-identical to `CEILING_RECORD_ONLY` and band and ceiling
sit side by side in every output record. The vocabulary is four bands either way; the
correspondence is documented at the definition site.

## 2. The three errata

| # | Correction | Where |
| --- | --- | --- |
| 1 | **My R4 §3 sentence was wrong.** It read "Four fixtures (S1, S5, S8, A11) pass under ceiling semantics." S1 passes under **plain equality** — its computed band is `none` and its expectation maps to `none`; the ceiling reading is load-bearing only for **S5, S8 and A11**. The same section wrote "Seven combinations failed on first run" when it was **seven fixtures = 21 combinations**. Both corrected here; the R4 sentences stand as written in that document and this is the erratum against them. | this record |
| 2 | README said "60-mutation" / "60 candidate defects". | `README.md:106`, `:249` — now **62** (61 after `interrupt-policy-id-fabricated`, 62 after `hub-visibility-lost`). |
| 3 | The `scenarios.py` Builder-added-stimuli enumeration claimed exhaustiveness while omitting S3's R4-added `placement_scope`/`proposed_action_class`. | `scenarios.py` — entry added, including why it was added and that no oracle field was consulted. |

All three are the RW-25 class: text not matching shipped files. That is now the second
consecutive cycle in which the defect found in my work was a claim/code mismatch
rather than a behavior defect, and erratum 1 is one I wrote *after* R4's §1 erratum
had already named the class. The check that would have caught it — re-reading each
claim against the file it describes — is the one I said I had applied.

## 3. Two reviewer observations carried as disclosures (no code change)

1. **The two citation parsers are byte-identical copies.** Their independence is
   **structural**, not diverse: a change to one cannot drag the other along, which is
   what lets the judge disagree with the engine, and that is the property RW-26(a)
   needed. But a shared parsing blind spot — a `start_state` phrasing neither regex
   matches — would be invisible to both. Recorded in NOT-SIMULATED and the README.
2. **`hub`'s position in the attention order is moot** now the vocabulary is four
   bands. I checked for ordering-sensitive code that depended on the deleted index:
   the only one was the queue-admission threshold, which is fixed above and now cites
   §2.1's own definition instead of an index. No other comparison depended on the
   gap.

## 4. Acceptance criteria — 16 re-proven

All PASS. Anti-circularity; 81/81 combinations, 0 unclassifiable, **0 judged
failures**; 171 evaluations over 56 predicates, 56 reachable, 0 NOT-EVALUABLE; 0
receipt-ownership violations; 81/81 order-invariant over 6 permutations; 81
divergences; E2E-1 with the seeded leak detected; 9/9 named defect classes; 8b 56/56
via a **62-mutation** catalogue; P2S-05 5/5 discriminating; P2S-07 2/2; 12 — 11/11
composition cases flipping; 13 — 15/15 judge checks flippable, 0 orphaned switches, 0
dead mutations; 14 — the D-B5 rule shown load-bearing; **15 — 66/81 attention
comparisons, 15 unmapped, 0 unresolved.**

Determinism: **10/10 outputs byte-identical** across consecutive runs. Hygiene: 28
files, 0 CR, 0 trailing whitespace, single final LF. Allowlist: 28 files, all inside
`design/traces/behavioral/`. Dead-code scan: no unused imports, no unreferenced
private helpers, **no residual reference to the deleted band**.

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | Every judge check and predicate can fail | A check or predicate with no witness. Gated: 15/15 and 56/56. The hub-visibility flag has its own witness rather than riding on the band's. | Not disconfirmed |
| 2 | Witness pairings are causally right | A pairing where defect and detection are only incidentally aligned. Five cycles, and each one removed at least one. Complete witness lists make sampling cheap; **hand-checking remains the only real assurance.** | **Explicitly unverified by me** |
| 3 | No witness is an artifact | A mutation writing a channel only its predicate reads. The tripwire covers 7 known forms over 2 known channels and says what it does not cover. | Not disconfirmed; **limit stated** |
| 4 | My record matches my code | A claim here the shipped files do not support. **This has now failed in two consecutive cycles** (R3's disjunct sentence, R4's S1/ceiling sentence). I re-checked every claim in §1–§4 against the file before writing it, which is exactly what I said last time. Treat my assurance on this row as worth less than a reviewer's diff. | **Failed twice; re-checked, not proven** |
| 5 | The attention mapping is faithful | A fixture §2.1 settles differently than I mapped it, or a ceiling reading that should be an equality. The ceiling split (grounded in A11's and S5's own receipts) and the A14 trigger-scope note above are the two judgment calls in it. | **Explicitly unverified by me** |
| 6 | The S3 and S9 corrections are faithful | An encoding that smuggles an outcome, or an engine rule that keys on a fixture. Fable's fifth-cycle review adjudicated both directly and found them genuine; that is stronger evidence than anything I can offer, and it is not my claim to make. | **Independently adjudicated (Fable), not by me** |
| 7 | The NOT-SIMULATED list is complete | A mechanism neither exercised nor listed. This closure added ATT-03's uncoded mappings and the parser-independence disclosure, and rewrote the entry the hub ruling made false. Incomplete at every prior cycle. | **Explicitly unverified by me** |
| 8 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file outside `design/traces/behavioral/`. 10/10 identical; 28 files, all inside. | Not disconfirmed |

## 6. Open items carried to Fable

1. **ATT-03 trigger scope** (§1) — one line from Fable settles whether the enumerated
   trigger list is exhaustive. A14 passes either way; only the *justification* for its
   hub flag changes.
2. **The D-B5 row-level granularity limit** — unchanged, and Fable's to carry to the
   verifier: my rule refuses consequential classes under any degradation where D-B5
   assigns per-failure-row safe modes.
3. **Residual-risk item from `23_` §carried-to-verifier** (rule-table branches
   mirroring fixture routes) remains open, as every packet since has also left it.

## 7. Deviations

- **No scope deviations.** Nothing outside `design/traces/behavioral/` written; no
  design document, gate artifact, trail, registry or checksum touched.
- **Branch deviation (unchanged, disclosed):** operator-designated branch rather than
  a task-specific one.
- **Recommended reviewer focus:** the 6 changed combinations (S7, A14 × 3 shapes) and
  the A14 trigger-scope note. Everything else on the other 75 is byte-identical to the
  R4 return you already adjudicated.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
