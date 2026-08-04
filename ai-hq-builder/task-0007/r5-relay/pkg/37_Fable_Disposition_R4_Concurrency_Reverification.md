# 37 — Fable Disposition: R4 concurrency re-verification

**Input:** `36_`/`36A_`/`36B_` + 24 probe artifacts (bundle SHA-256 `17fba2e3b4c5e83e7071126c2bacd249721bf730717dffe15cf18e79f2668c19`; internal `SHA256SUMS` **28/28 valid**). Verdict: **FAIL — one new High finding**, with everything else closed.

## 1. What closed

- **AUDIT-R4-5: CONCUR, criterion formally amended by the verifier.** It states it *cannot* produce a conforming implementation of the selected model in which both requests reach the injected points, and enumerates the four ways one could be forced — each of which either changes the architecture, evades the probe, or concedes the amendment. Fable's ruling is confirmed and, importantly, the record now shows **the verifier amended its own criterion**, which is what `35_` asked for.
- **SEC-R3-01 and SEC-R3-02: CLOSED for R4.** One winner per identity, and — better than cardinality alone — the *loser responses truthfully describe the winner's already-effective state* (`already-registered`, `duplicate-suppressed`, `refused-token`, replay-with-no-second-side-effect, `duplicate-run-declaration`).
- **Beyond two requests:** a supplemental **8-way** check passed, closing a gap the Builder explicitly did not claim.
- **Deadlock:** no present cycle found; the posture remains structural and unenforced, as disclosed.

## 2. A correction to Fable's own ruling, owned

`34_` accepted `barrier_suite.py` as **equivalent** evidence. The verifier accepts the amendment but **downgrades that suite to corroborating, not controlling**: its `race()` helper aligns two *clients* immediately before sending, which aligns intent but does not deterministically force both requests to the same server-side precondition — OS scheduling may still serialize them.

It then built the right instrument: a **live-HTTP handler-entry release gate** that wraps the real handler without bypassing auth, route policy, preconditions, transition code, capture code, or final state checks. In R4 exactly one handler enters before release; against pinned R3 both enter and the duplicate-authority behaviour reproduces.

**Fable concurs and corrects the record.** The ruling's direction was right — the criterion did need amending — but calling a client-side barrier "equivalent" over-claimed what it proves. The controlling evidence is the verifier's handler-entry gate, and that distinction is adopted: **a barrier that aligns clients is not a barrier that aligns transitions.**

## 3. SEC-R4-01 — CONCURRED, gate-blocking

A residual of SEC-R3-05 with SEC-R3-03 impact. `write_capture` sets `published = True` **after** `os.link` succeeds but **before** the directory fsync. If the directory open/fsync then fails, the `finally` block sees `published == True`, so it **keeps the quota unit and leaves the final file in place** — a record reading `phase: committed`, `outcome: committed`, `final_status: REGISTERED` for a transition the service rolled back out of live state. False durable authority evidence, which is precisely what A.7 exists to prevent. A separate ordering also leaves the final hard link when the temp unlink fails.

Independently reproduced at three boundaries (directory-fsync failure, directory-open failure, temp-unlink failure): one final JSON file left in every case; a quota unit retained in two.

The no-overwrite property itself is confirmed correct — `os.link` failing on an existing path is the right primitive, and that part of SEC-R3-05 stands closed. **The defect is entirely in what happens after the link succeeds.**

## 4. Disposition and next step

R4's concurrency architecture is **accepted and is not reopened** — the verifier says so explicitly. `38_` issues one narrow capture-publication correction to the Builder: publication is not "published" until the directory fsync has succeeded; any failure after the link must remove the final path *and* release the quota; the temp-unlink path must clean the final link too; and fault tests are required at every post-link boundary (link, temp-unlink, directory-open, directory-fsync), each demonstrated failing against the pinned R4 artifact.

Owner POC session remains **BLOCKED** on that one fix and its re-check. Nothing else is open.
