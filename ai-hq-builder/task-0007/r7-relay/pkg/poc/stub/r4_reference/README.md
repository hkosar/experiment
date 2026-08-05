# Pinned R4 baseline — do not edit

`stub_server_r4.py` is a byte-identical copy of the stub returned at R4
(`sha256 2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79`), the
build the verifier examined when it raised SEC-R4-01.

`38_` requires the R5 fault tests to be demonstrated failing against it, pinned
exactly as `r3_reference/` is. `probe_runner.py` and `selftest_stub.py` verify
this digest before loading the file and refuse to continue on a mismatch.

`38_` §"Unchanged" names `r4_reference/` as a permitted addition on the
established precedent; it is listed in `RETURN_MANIFEST.json`. Nothing here is
executed by the shipped service.
