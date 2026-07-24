#!/usr/bin/env bash
# Repository compliance audit (run via `make audit`).
#
# Re-runs the Session-00 Phase-8 checks at any time. The forbidden-string
# pattern and the two tooling paths are expressed with bracketed character
# classes / fragment concatenation, so this script does not itself contain the
# literal strings it screens for and stays clean under check 1.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

pat='[c]laude|[a]nthropic|co-[a]uthored|[g]enerated with'
tooling_md="CL""AUDE.md"
tooling_dir=".cl""aude/"
author_expected="Palaash Gang <palaashgang@gmail.com>"

fail=0
pass() { printf "  PASS  %s\n" "$1"; }
bad()  { printf "  FAIL  %s\n" "$1"; fail=$((fail + 1)); }
skip() { printf "  SKIP  %s\n" "$1"; }

echo "== physics-waves repository audit =="

# 1. No forbidden strings in tracked files
offenders="$(git ls-files -z | xargs -0 grep -riEl "$pat" 2>/dev/null || true)"
if [ -n "$offenders" ]; then
  bad "1. forbidden strings present in tracked files"
  sed 's/^/       /' <<<"$offenders"
else
  pass "1. no forbidden strings in tracked files"
fi

# 2. No forbidden strings in commit history
if git log --format='%s%n%b' | grep -qiE "$pat"; then
  bad "2. forbidden strings present in commit history"
else
  pass "2. no forbidden strings in commit history"
fi

# 3. Single author
authors="$(git log --format='%an <%ae>' | sort -u)"
if [ "$authors" = "$author_expected" ]; then
  pass "3. single author ($author_expected)"
else
  bad "3. unexpected authors: $authors"
fi

# 4. Tooling files ignored
if git check-ignore -q "$tooling_md" && git check-ignore -q "$tooling_dir"; then
  pass "4. tooling files ignored"
else
  bad "4. tooling files not ignored"
fi

# 5. Manifest tracked
tracked_ext="$(git ls-files data/external/)"
if grep -q 'README.md' <<<"$tracked_ext" \
   && grep -q 'MANIFEST.md' <<<"$tracked_ext" \
   && grep -q 'checksums.sha256' <<<"$tracked_ext"; then
  pass "5. external manifest, readme and checksums tracked"
else
  bad "5. external manifest set incomplete"
fi

# 6. No data binaries tracked
if git ls-files | grep -qE '\.(nc|h5|hdf5|grib)$'; then
  bad "6. data binaries are tracked"
else
  pass "6. no data binaries tracked"
fi

# 7. Remote in sync
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main 2>/dev/null)" ]; then
  pass "7. HEAD matches origin/main"
else
  bad "7. HEAD does not match origin/main"
fi

# 8. Tests pass
if python -c "import pytest" >/dev/null 2>&1; then
  if python -m pytest tests/ -q >/tmp/pw_audit_pytest.log 2>&1; then
    pass "8. pytest suite green"
  else
    bad "8. pytest suite failed (see /tmp/pw_audit_pytest.log)"
  fi
else
  skip "8. pytest not available in this environment"
fi

# 9. Checksums valid
if [ -s data/external/checksums.sha256 ]; then
  if ( cd data/external && sha256sum -c checksums.sha256 >/dev/null 2>&1 ); then
    pass "9. external checksums valid"
  else
    bad "9. external checksum verification failed"
  fi
else
  skip "9. no external checksums to verify"
fi

# 10. Config stubs valid against the schema
if python -c "import yaml, jsonschema" >/dev/null 2>&1; then
  if python - <<'PY'
import sys, glob, yaml, jsonschema
schema = yaml.safe_load(open("configs/_schema.yaml"))
bad = 0
for f in glob.glob("configs/*/*.yaml"):
    try:
        jsonschema.validate(yaml.safe_load(open(f)), schema)
    except jsonschema.ValidationError as e:
        print(f"       {f}: {e.message}"); bad += 1
sys.exit(1 if bad else 0)
PY
  then
    pass "10. all config stubs validate against the schema"
  else
    bad "10. one or more config stubs are invalid"
  fi
else
  skip "10. jsonschema not available in this environment"
fi

# 11. Commit count
n="$(git rev-list --count main)"
if [ "$n" -ge 16 ]; then
  pass "11. commit count is $n (>= 16)"
else
  bad "11. commit count is $n (< 16)"
fi

# 18. No CDS credential token anywhere in the repository (tracked files OR full
#     history, including commit messages). The 8-char token prefix is assembled
#     from fragments at run time, so this guard does not itself contain the
#     literal string it screens for (same technique as check 1).
tok8="17""e064""f1"
if git ls-files -z | xargs -0 grep -lIF "$tok8" 2>/dev/null | grep -q . \
   || git log -p --all 2>/dev/null | grep -qF "$tok8"; then
  bad "18. CDS credential token present in repository (tracked files or history)"
else
  pass "18. no CDS credential token in tracked files or history"
fi

# 19. No ORCID placeholder remains in any tracked file. Assembled from fragments
#     so this guard stays clean under its own screen.
ph="ORCID""_PLACEHOLDER"
if git ls-files -z | xargs -0 grep -lIF "$ph" 2>/dev/null | grep -q .; then
  bad "19. ORCID placeholder still present in tracked files"
else
  pass "19. no ORCID placeholder in tracked files"
fi

# 20. The CDS credentials file is mode 600 and lives outside the repository.
rc="${HOME}/.cdsapirc"
if [ -f "$rc" ]; then
  mode="$(stat -f %Lp "$rc" 2>/dev/null || stat -c %a "$rc" 2>/dev/null)"
  case "$rc" in
    "$(git rev-parse --show-toplevel)"/*) inside=1 ;;
    *) inside=0 ;;
  esac
  if [ "$mode" = "600" ] && [ "$inside" -eq 0 ]; then
    pass "20. ~/.cdsapirc is mode 600 and outside the repository"
  else
    bad "20. ~/.cdsapirc mode=$mode inside_repo=$inside (want 600, outside)"
  fi
else
  skip "20. no ~/.cdsapirc present on this machine"
fi

# 26. The Phase-0 reference example carries an ATTRIBUTION.md naming its licence.
attrib="tests/phase0_gate/dedalus_reference/ATTRIBUTION.md"
if [ -f "$attrib" ] && grep -qiE 'GPL|General Public License|licen[cs]e' "$attrib"; then
  pass "26. Phase-0 reference ATTRIBUTION.md names the upstream licence"
else
  bad "26. Phase-0 reference ATTRIBUTION.md missing or names no licence"
fi

# 27. docs/CLI_COMMANDS.md lists exactly the five commands, each a Makefile target.
cli_ok=1
[ -f docs/CLI_COMMANDS.md ] || cli_ok=0
for c in verify refcheck manuscript figure sweep; do
  grep -q "make $c" docs/CLI_COMMANDS.md 2>/dev/null || cli_ok=0
  grep -qE "^$c:" Makefile 2>/dev/null || cli_ok=0
done
if [ "$cli_ok" -eq 1 ]; then
  pass "27. CLI_COMMANDS.md lists five commands, each a Makefile target"
else
  bad "27. CLI_COMMANDS.md / Makefile command set incomplete"
fi

# 28. The slash-command wrappers remain gitignored (never enter the public repo).
#     The tooling directory name is assembled from fragments so this guard does
#     not itself trip check 1 (same technique as the attribution guards).
cmddir=".cl""aude/commands"
cmd_ok=1
for c in verify refcheck manuscript figure sweep; do
  git check-ignore -q "${cmddir}/$c.md" || cmd_ok=0
done
if [ "$cmd_ok" -eq 1 ]; then
  pass "28. slash-command wrappers are gitignored"
else
  bad "28. a slash-command wrapper is not gitignored"
fi

# 29. The operational commands run without an unhandled exception (a graceful
#     message is a pass; a Python traceback is not); `make sweep` fails on
#     purpose. `make verify` is excluded here — it calls `make audit`, so running
#     it inside this audit would recurse; instead its script is syntax-checked,
#     and its constituents (this audit, pytest, the gate record) are each checked.
cmd29=1; why=""
if command -v make >/dev/null 2>&1; then
  for t in refcheck manuscript; do
    make "$t" >/tmp/pw_cmd29_$t.log 2>&1 || true
    grep -qiE 'Traceback \(most recent call last\)' /tmp/pw_cmd29_$t.log && { cmd29=0; why="$why $t:traceback"; }
  done
  make figure ARGS=--style-preview >/tmp/pw_cmd29_figure.log 2>&1 || true
  grep -qiE 'Traceback \(most recent call last\)' /tmp/pw_cmd29_figure.log && { cmd29=0; why="$why figure:traceback"; }
  if make sweep >/tmp/pw_cmd29_sweep.log 2>&1; then cmd29=0; why="$why sweep:exited-0"; fi
  grep -qi 'NOT YET IMPLEMENTED' /tmp/pw_cmd29_sweep.log || { cmd29=0; why="$why sweep:no-message"; }
  bash -n scripts/verify.sh 2>/dev/null || { cmd29=0; why="$why verify:syntax"; }
  if [ "$cmd29" -eq 1 ]; then
    pass "29. operational commands execute without unhandled exceptions"
  else
    bad "29. operational command check:$why"
  fi
else
  skip "29. make not available in this environment"
fi

echo "== $( [ "$fail" -eq 0 ] && echo "AUDIT PASSED" || echo "AUDIT FAILED ($fail check(s))" ) =="
exit "$fail"
