# 38 — TASK-0007 Round R5: capture-publication correction (SEC-R4-01)

**Scope: one defect.** The concurrency architecture from R4 is **accepted and must not be reopened** — the verifier states this explicitly (`36_` §1). `25_` is unchanged. This is the narrowest round in the program.

## The defect

`write_capture` sets `published = True` immediately after `os.link(tmp, final)` succeeds, but **before** the directory fsync. A failure at directory open/fsync therefore leaves the `finally` block believing publication succeeded: it **retains the reserved quota unit and leaves the final file on disk**, even though the service rolled the transition out of live state. The surviving record reads `phase: committed`, `outcome: committed`, `final_status: REGISTERED` — false durable authority evidence for a transition that did not become effective. Separately, if the temp unlink fails after a successful link, cleanup retries only the temp name and the final hard link survives.

Independently reproduced at three boundaries: forced directory-fsync failure, forced directory-open failure, forced temp-unlink failure. One final JSON left in every case; quota retained in two.

## Required correction

1. **A capture is not published until the directory fsync has succeeded.** Move the `published = True` assignment after the directory fsync completes — or, equivalently, track publication as durable only past that point.
2. **Any failure after the link must remove the final path** as well as the temp, so no success-named record survives a rolled-back transition.
3. **Any failure after the link must release the reserved quota unit** — including the reserved-owner pool. `33_` §1's rule stands: a failed step rolls back with no observable effect and **no consumed resource**.
4. **The temp-unlink failure path must also clean the final link**, not only retry the temp name.
5. Keep `os.link` — the no-overwrite property is confirmed correct and that part of SEC-R3-05 is closed.

## Required tests

Fault injection at **every post-link boundary** — the link itself, temp unlink, directory open, directory fsync — each asserting: no final file left, no quota consumed, no committed record surviving for a rolled-back transition. Demonstrate each failing against the **pinned R4 artifact** using the standing method: pin R4 as `r4_reference/` exactly as `r3_reference/` is pinned, and require red before green. The verifier's own `chatgpt_capture_publication_fault_probe.py` and `chatgpt_capture_postlink_cleanup_probe.py` ship in this packet at `36_security_probes/` and must run green.

## Unchanged

Allowlists, immutable denylist (`r1_/r2_/r3_reference`, harness code, `authority_manifest.json`), the global-lock architecture, the `Disclose` exemption, and every THROWAWAY marker. `r4_reference/` is a permitted addition on the established precedent — list it in the return manifest.

**Stop and report** if the fix cannot be made without touching the concurrency model. It should not need to; the defect is confined to the publication ordering inside `write_capture`.

## After R5

Builder → Fable structural verification → verifier re-check of this one finding → **owner hands-on POC session.**
