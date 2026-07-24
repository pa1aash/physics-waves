#!/usr/bin/env bash
# make verify: one consolidated repository verification.
#
# Runs, in order: the full compliance audit, the test suite, and a check that the
# Phase-0 toolchain-validation gate is still recorded PASSED. Exits non-zero if
# any stage fails, naming which. Its power grows automatically as later sessions
# add audit checks and tests — it only calls those entry points.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

fails=""
note() { printf "[verify] %-14s ... %s\n" "$1" "$2"; }

# 1. compliance audit
if bash scripts/audit.sh >/tmp/pw_verify_audit.log 2>&1; then
  note audit OK
else
  note audit "FAIL (see /tmp/pw_verify_audit.log)"; fails="${fails:+$fails,}audit"
fi

# 2. test suite
if python -m pytest tests/ -q >/tmp/pw_verify_tests.log 2>&1; then
  note tests OK
else
  note tests "FAIL (see /tmp/pw_verify_tests.log)"; fails="${fails:+$fails,}tests"
fi

# 3. Phase-0 gate record still PASSED
if grep -qiE 'phase[- ]0 gate[^A-Za-z]*passed' docs/CONVENTIONS.md 2>/dev/null; then
  note phase-0-gate OK
else
  note phase-0-gate "FAIL (docs/CONVENTIONS.md no longer records Phase-0 gate PASSED)"
  fails="${fails:+$fails,}phase-0-gate"
fi

if [ -z "$fails" ]; then
  echo "VERIFY: PASSED"; exit 0
else
  echo "VERIFY: FAILED ($fails)"; exit 1
fi
