# Pinned R5 baseline — do not edit

`stub_server_r5.py` is a byte-identical copy of the stub returned at R5
(`sha256 972c30d532a957a94a8e7200c9385e387f7508673335acdc8652eb6e3dd15e68`), the
build the verifier examined when it held SEC-R4-01 open.

`42_` requires every R6 criterion to be shown **red against this pin** before it
is claimed green. `probe_runner.py`, `capture_fault_suite.py` and
`selftest_stub.py` verify this digest before loading the file and refuse to
continue on a mismatch.

`42_` names `r5_reference/` as a permitted addition on the established
precedent; it is listed in `RETURN_MANIFEST.json`. Nothing here is executed by
the shipped service.
