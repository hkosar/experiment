#!/usr/bin/env bash
# Re-runs every check in this harness and writes machine-readable output to out/.
# Safe to run before the owner session (everything reports NOT TESTED) and after
# (the same checks consume the captured measurements).
set -u
cd "$(dirname "$0")"
mkdir -p out
fail=0

# The n8n library is not vendored into the return (it is ~90 packages and carries
# no evidence). Install it once before the first run:
if ! node -e "require('n8n-workflow')" >/dev/null 2>&1; then
  echo "n8n-workflow is not installed. Run this once, from this directory:"
  echo "    npm install n8n-workflow"
  echo "Everything except the two structural checks will still run."
fi

run() {  # run <label> <outfile> <cmd...>
  printf '\n=== %s ===\n' "$1"
  shift
  out="$1"; shift
  if "$@" > "out/$out" 2>"out/${out%.json}.log"; then
    cat "out/${out%.json}.log"
  else
    cat "out/${out%.json}.log"; fail=1
  fi
}

run "n8n structural validation"      structural.json        node validate_n8n_workflows.mjs
run "validator self-test"            validator_selftest.json node selftest_validator.mjs
run "boundary compliance"            boundary.json          python3 check_boundaries.py
run "boundary self-test"             boundary_selftest.json python3 check_boundaries.py --self-test
run "cost model"                     cost_model.json        python3 cost_model.py
run "cost model self-test"           cost_selftest.json     python3 cost_model.py --self-test
run "receipt conformance"            receipt.json           python3 receipt_conformance.py
run "receipt self-test"              receipt_selftest.json  python3 receipt_conformance.py --self-test
run "D-EC_ field inventory"          receipt_fields.json    python3 receipt_conformance.py --fields

printf '\n=== HARNESS %s ===\n' "$([ $fail -eq 0 ] && echo PASS || echo FAIL)"
printf 'NOTE: passing means the definitions and the arithmetic are sound.\n'
printf 'It does NOT mean any POC has been run. No provider was contacted.\n'
exit $fail
