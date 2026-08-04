# 29 — Fable Disposition: TASK-0007 R3 Builder return

**Input:** `TASK0007_R3_Builder_Return.zip`, SHA-256 `48171f38b6f81e37f621a73cc4e643ed45f301ef5717926d39255754f9bf6081` — matching the Builder's stated fingerprint.

## 1. Structural verification (static only, per the trail-127 practice)

| Check | Result |
| --- | --- |
| Return zip vs Builder's stated fingerprint | **MATCH** |
| `RETURN_MANIFEST.json` re-hashed entry by entry | 47 entries — **45 match, 0 missing, 2 differ** (see §1.1) |
| Files under `poc/` not declared in the manifest | **0** |
| Harness **code** unchanged (immutable denylist) | **6/6 byte-identical** |
| `r1_reference/stub_server_r1.py` | `ecdaae67…76328ac` — **still the exact R1 target the verifier reviewed** |
| `r2_reference/stub_server_r2.py` vs the integrated R2 stub | `a2aea25d…` — **byte-identical; the new pin is genuine** |
| Stdlib-only across `stub_server.py`, `selftest_stub.py`, `r1_witnesses.py`, `validate_measurements.py` | **confirmed** |
| Secret-shaped scan across the R3 tree | **clean** |
| Self-test / witnesses, as returned | **167/167**, **34/34**, zero failures |

**Adversarial verification NOT performed by Fable**, by design: no server started, no self-test run, no witness suite run, no probe issued. Per the trail-127 practice that category routes to independent review. **The Builder's 167/167, 34/34 and 160/160 are Builder-authored self-claims** — undisputed, and not independently confirmed by this disposition.

### 1.1 The two manifest differences — benign, and a standing note

`stub/out/r1_witnesses.json` and `stub/out/selftest.json` differ from their declared hashes at **identical byte length**. Cause: these evidence files embed run-specific random identifiers (e.g. `case-5f6db1716382`), so a re-run produces equivalent-but-not-identical content. The Builder re-ran the suites for its §5 "every figure produced by a command run after the last edit" check *after* computing the manifest, and did not regenerate it. Contents verified equivalent: **167/167 and 34/34 with zero failures in the shipped files**.

Ruled a **process slip, not a defect** — the same class as Fable's own trail-122 slip. **Standing note adopted:** `out/**` evidence is non-deterministic by construction and cannot be hash-pinned across runs; future manifests should either be regenerated last or explicitly mark `out/**` as re-run-volatile.

## 2. The finding that lands on Fable: DEF-R2-01

**The R2 stub — which Fable structurally accepted and integrated as the baseline (trail 130) — could not hand out the credentials it minted.** Every response passed through the same redaction as a capture, so `resume_token` and `execution_capability` returned as `{"__withheld__": …}` descriptors. **POC-1 was unrunnable over HTTP.** The owner's hands-on session would have failed at its first step.

**Fable reproduced this independently** (pure-function check on the integrated R2 module; no server, no adversarial probe):

```text
minted token          FNyqw2YxRMGuzmz6JeCC…
what a provider gets  {'__withheld__': 'secret-key-name', 'name': 'resume_token', …}
TOKEN USABLE          False
capability returned   [REDACTED:live-secret]
CAPABILITY USABLE     False
_is_secret_key('resume_token') = True ; in NON_SECRET allowlist = False
```

**Why three layers of review missed it.** The Builder's R2 self-test passed 56/56 because it called `dispatch()` in-process — one layer below `_respond`, where the loss occurred. ChatGPT's security review examined the authorization boundary, which was sound. **And Fable read `_respond`, saw `json.dumps(redact(body))`, and did not ask what `redact` does to the token that response exists to deliver.** That is a Fable verification defect, not merely a missed Builder defect: the trail-130 disposition asserted the R2 build was structurally sound while its primary function was broken. Static reading confirms shape and provenance; it does not confirm that the thing works. That limit was stated in trail 130 and is now demonstrated rather than theoretical.

**Recorded consequence:** "structurally accepted" has meant *provenance and shape verified, function unverified* throughout this program. Going forward that phrase must not be read as any claim about whether the artifact works.

The Builder's fix is a `Disclose` marker unwrapped **on the response path only**, identity-based rather than key-name-based — so a caller cannot name its way past redaction, and a `Disclose` still reduces to a descriptor on the capture path. Fable notes the Builder's own falsifier row 4 flags this as a real hole in redaction by construction, safe today but not self-protecting against a future edit that wraps the wrong value. **That is the single item Fable most wants the independent security review to attack.**

## 3. Rulings on the four §F audit findings

**AUDIT-1 — CONFIRMED, and it is a Fable contract defect.** A.4's `UNCERTAIN` trigger read *"(provider reports uncertain, or timeout)"*, naming a **provider-supplied value** as the trigger for an authority-bearing transition. That contradicts the governing rule and A.6's rule that `/poc1/receipt` cannot alter capability state — and since `provider_status` exists only on receipt routes, the clause was unimplementable as written. The Builder's resolution (UNCERTAIN reachable only by service-established means: its own expiry observation, or a delivery whose `committed` record did not land) is **correct and forced**. **A.4 is amended; A.6 stands.** Verified in the build: `/poc1/receipt` records `action_request_status_changed: False` and refuses a late receipt on `REVOKED`/`EXPIRED` with a captured 409.

This is the **fifth** instance of the same Fable failure family: naming an authority without tracing what establishes it. It was caught this time by the Builder's pre-build contract audit — a control that has now justified itself.

**AUDIT-2 — CONFIRMED.** §B's "Quota pool" column named the per-entity ceilings while A.8 defines three *capture* pools; one column name covered two axes. The Builder's two-axis implementation is right. **Column renamed "Entity quota"**; A.8's three pools are unchanged.

**AUDIT-3 — ACKNOWLEDGED, no action.** `submission_epoch` is a deliberate duplicate-suppression escape and the Builder read its purpose correctly. Recording it prevents a later reader mistaking it for an oversight, and the distinction between `attempt` and `submission_epoch` matters to a provider-discriminating measurement.

**AUDIT-4 — ACCEPTED.** `poc/stub/r2_reference/` (2 files) sits outside §0's enumerated implementation allowlist because **§0 had nowhere to put it** while §E requires the R2 baseline pinned — a Fable allowlist gap. The files mirror the accepted `r1_reference/` pattern exactly (byte-identical copy, run-time digest check, never executed by the service), and the pin is verified genuine above. Accepted and now part of the baseline; the immutable denylist extends to it.

Both amendments to `25_` are recorded **visibly inside `25_` itself** as a post-build amendment record, so the independent security review can confirm the amended text matches the build it reviews. Neither introduces a new requirement; the returned build already conforms to both.

## 4. What the Builder found in its own draft, recorded

**DEF-R3-01:** two §E-required refusals (`rejected-unauthorized-target`, `rejected-unknown-target`) were dead code behind the A.2 binding check. Fixed by ordering A.1's role verdicts before A.2's binding, and guarded mechanically by an outcome-coverage test that enumerates every outcome code the source can emit and fails if any is never produced — **that guard then found seven more unexercised outcomes.** Three further defects found the same way: `/poc1/reconcile` moved a `MINTED` capability to `UNCERTAIN` (a transition A.4 does not list, and one a provider could use to strand its own authorization and then present the result as grounds for an owner attestation); the relay's attempt counter and single permitted re-attempt were consumed *before* their `prepared` record landed, so a capture failure could burn a provider's one retry with nothing attempted; and `write_capture` inferred provenance from a name list, silently filing every newly minted field as provider-supplied.

The outcome-coverage guard is the notable artifact here — a mechanical control against exactly the "control exists but is unreachable" class this program has hit repeatedly. Fable adopts it as a pattern worth carrying into the real wrapper's build.

## 5. Disposition and sequencing

**The R3 return is STRUCTURALLY ACCEPTED and INTEGRATED** as the new `poc/` baseline (4 added, 14 modified; manifest reconciled; `r2_reference/` accepted per AUDIT-4). Its **security posture is NOT independently verified**, and no acceptance of any security property is claimed here.

**Next, per `25_` §G:** the combined **R2+R3 stub goes to ChatGPT for the single independent security review** this contract has been building toward. Fable assembles the packet and dispositions the result; Fable does not run the probes. Fable's requested reviewer focus, in order: (1) the `Disclose` redaction exemption (Builder falsifier row 4 — a deliberate hole, argued safe, and the newest attack surface); (2) whether the R2-class defect has an R3 analogue — a control whose *tested layer* differs from the layer a caller meets; (3) the AUDIT-1 amendment as built versus as now written; (4) the two-phase evidence ordering at the transitions §E does not enumerate, which the Builder states hold "by construction" and which it has already twice found not to.

On that review closing: the owner's hands-on POC session. **Owner POC session remains BLOCKED** until it does. Provider selection NOT MADE. Release-1, the Capability Portfolio work, the Decision Engine baseline and v1.4 all stand unreopened; the v1.4 owner one-line acceptance remains outstanding.
