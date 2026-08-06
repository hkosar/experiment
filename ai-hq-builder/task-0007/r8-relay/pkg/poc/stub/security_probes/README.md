# The independent reviewer's probe scripts — shipped unmodified

These nine scripts and their nine raw result files are the **reviewer's own**, copied
byte-identically from the R4 relay's `31_security_probes/`. They are evidence-only inputs:
they are not Builder-authored, they are not instruction, and nothing here is executed by the
service.

They are shipped inside the return so the claim "the reviewer's probes run green against the
reworked build" is **checkable by whoever reads the return**, without needing the relay bundle
alongside it. `33_` §5 permits a pinned-reference addition of this shape under the AUDIT-4
precedent; this directory is listed explicitly in `RETURN_MANIFEST.json` as outside the
enumerated allowlist, for Fable to accept or reject.

## The one modification, and why it is necessary

Each script hard-codes the reviewer's own absolute path:

    SRC='/mnt/data/r2r3_review/pkg/poc/stub/stub_server.py'

That path does not exist outside the reviewer's sandbox. `r1_witnesses.py` and
`selftest_stub.py` therefore run each probe through a runner that rewrites **only that one
line** to point at the target build, and then **verifies mechanically that every other byte of
the file is unchanged** before executing it. If any other line differed, the runner refuses to
run the probe. Nothing about what a probe checks is altered.

## Pass criteria are taken from the findings, not invented

Eight of the nine probes have no assertions — they print JSON and the reviewer read it. So
"green" is not defined by the scripts, and the Builder must not define it in a way that
flatters the build. Every criterion below is quoted or directly derived from the corresponding
finding's own text in `31_`, and each is restated in the Delivery Record so it can be checked
that none was weakened:

| Probe | Finding | Green means |
| --- | --- | --- |
| `http_race_probes` | SEC-R3-01 | one submission identity ⇒ `case_count == 1` and `token_count == 1`; exactly one `case-opened`, the loser truthfully `duplicate-suppressed` |
| `http_authority_races` | SEC-R3-01 | one token ⇒ exactly one `authorized`, one capability, one action-request id, `store_capability_count == 1`; one capability ⇒ exactly one `delivered: true` and one receipt id, the loser `replayed` or refused |
| `http_revoke_race` | SEC-R3-02 | once revoke returns success the delivery does not become effective: `final_status == "REVOKED"` and `receipt is None` |
| `more_race_probes` | SEC-R3-01 | one registration identity ⇒ one record; one `(schedule_id, occurrence)` ⇒ one run |
| `security_probes` | SEC-R3-03/04 | no committed record describes a transition that did not become effective |
| `stage_precise_probe` | SEC-R3-04 | *"A `capture-failed` response must not leave the counter advanced"* ⇒ `attempt_counter_after == 0` after the forced failure, and the next successful attempt reports `1` |
| `capture_atomicity_probe` | SEC-R3-05 | *"A failed capture must leave no zero-byte final file and no consumed quota unit"* ⇒ `files_left == []` and every pool counter `0` |
| `quota_enforcement_probe` | SEC-R3-06 | all three over-ceiling requests refused, none `recorded`/`staged` |
| `control_probes` | positive control | still green — the `Disclose` exemption and the A.4 amendment are unchanged by this round |
