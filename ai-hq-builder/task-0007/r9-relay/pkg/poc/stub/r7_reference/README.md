# Pinned R7 baseline — do not edit

`stub_server_r7.py` is a byte-identical copy of the stub returned at R7, the
build the verifier executed for the R8 findings (`49_`, concurred in `50_`).

`sha256 69b98fb09ae94d4f38b30e3e2d2179045fe4e50b529033940a7ad1ccf6b0ac91` — the
value the verifier and Fable both independently report for that build.

`51_` §4 makes red-before-green mandatory and adds the standing anti-evasion
check: every criterion is shown failing against this pin **and** the injected
fault is shown landing identically on both builds, so a green result cannot come
from a build that routed around the injection point. The suites verify this
digest before loading the file and refuse to continue on a mismatch.

`51_` §5 names `r7_reference/` as a permitted addition and §3 adds it to the
immutable denylist for every round after this one. Nothing here is executed by
the shipped service.
