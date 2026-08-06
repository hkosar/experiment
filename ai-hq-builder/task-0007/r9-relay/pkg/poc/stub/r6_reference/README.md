# Pinned R6 baseline — do not edit

`stub_server_r6.py` is a byte-identical copy of the stub returned at R6, the
build the verifier examined for the R7 findings.

`46_` makes red-before-green mandatory: every R7 criterion is shown failing
against this pin before it is claimed green. The suites verify this digest
before loading the file and refuse to continue on a mismatch.

`46_` names `r6_reference/` as a permitted addition on the established
precedent; it is listed in `RETURN_MANIFEST.json`. Nothing here is executed by
the shipped service.
