# Pinned R8 baseline — do not edit

`stub_server_r8.py` is a byte-identical copy of the stub returned at R8, the
build the verifier executed four times for the R9 findings (`54_`, concurred in
`55_`).

`sha256 5df1408fdf2fd5dbcb5d2577a20c14699009493c32de1ba7c0d6c347c44bf7a1`

`56_` §4 makes red-before-green mandatory against this pin, with the standing
anti-evasion check: the injected fault must be shown firing identically on both
builds, so a green result cannot come from a build that routed around the
injection point. The suites verify this digest before loading the file and
refuse to continue on a mismatch.

`56_` §4 names `r8_reference/` as a permitted addition and adds it to the
immutable denylist for every round after this one. Nothing here is executed by
the shipped service.
