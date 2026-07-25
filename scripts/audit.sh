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

# 1. No forbidden strings in tracked files.
#    The two literature pool CSVs are excluded and covered by check 1b instead:
#    they are machine-retrieved bibliographic metadata, and several real
#    researchers in this field carry a given name that collides with one of the
#    screened tokens. The blunt pattern cannot tell a person's name from a tool
#    byline. See docs/CONVENTIONS.md, authorised deviation 4.
pool_re='^(docs/literature/(CANDIDATE|VERIFIED)_POOL\.csv|manuscript/references\.bib)$'
offenders="$(git ls-files -z | grep -zEv "$pool_re" | xargs -0 grep -riEl "$pat" 2>/dev/null || true)"
if [ -n "$offenders" ]; then
  bad "1. forbidden strings present in tracked files"
  sed 's/^/       /' <<<"$offenders"
else
  pass "1. no forbidden strings in tracked files (pool CSVs -> check 1b)"
fi

# 1b. The excluded pool CSVs carry the forbidden tokens ONLY inside the authors
#     column. Anywhere else in those files -- title, venue, query string -- is a
#     real finding. Column 3 is `authors` in both files.
pool_bad=""
# manuscript/references.bib is generated from these CSVs, so it inherits the same
# author names and the same bounded exemption: the token may appear only inside an
# `author = {...}` field.
if [ -f manuscript/references.bib ]; then
  bibhits="$(python3 - manuscript/references.bib <<'PY_EOF'
import re, sys
txt = open(sys.argv[1], encoding="utf-8").read()
pat = re.compile(r"[c]laude|[a]nthropic|co-[a]uthored|[g]enerated with", re.I)
bad = []
for i, line in enumerate(txt.splitlines(), start=1):
    if pat.search(line) and not re.match(r"\s*author\s*=", line) and not line.lstrip().startswith("%"):
        bad.append(f"line {i}")
print("; ".join(bad))
PY_EOF
)"
  [ -n "$bibhits" ] && pool_bad="$pool_bad manuscript/references.bib:[$bibhits]"
fi
for f in docs/literature/CANDIDATE_POOL.csv docs/literature/VERIFIED_POOL.csv; do
  [ -f "$f" ] || continue
  hits="$(python3 - "$f" <<'PY_EOF'
import csv, sys, re
pat = re.compile(r"[c]laude|[a]nthropic|co-[a]uthored|[g]enerated with", re.I)
bad = []
with open(sys.argv[1], newline="", encoding="utf-8") as fh:
    for i, row in enumerate(csv.DictReader(fh), start=2):
        for k, v in row.items():
            if k != "authors" and v and pat.search(v):
                bad.append(f"line {i} column {k}")
print("; ".join(bad))
PY_EOF
)"
  [ -n "$hits" ] && pool_bad="$pool_bad $f:[$hits]"
done
if [ -z "$pool_bad" ]; then
  pass "1b. pool CSVs and references.bib carry tokens only in author fields"
else
  bad "1b. forbidden token outside authors column:$pool_bad"
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

# 30. Every derivation-verification script has a recorded verdict.
#     theory/derivations.tex may present nothing as established without a check
#     under theory/sympy_checks/ that actually ran, so an orphaned script — or a
#     stale one whose output was never regenerated — is a real finding.
if [ -d theory/sympy_checks ]; then
  cov_ok=1; missing=""
  shopt -s nullglob
  for f in theory/sympy_checks/check_*.py; do
    out="theory/sympy_checks/output/$(basename "${f%.py}").txt"
    if [ ! -f "$out" ]; then
      cov_ok=0; missing="$missing $(basename "$f"):no-output"
    elif ! grep -qE '^VERDICT: (VERIFIED|MISMATCH)$' "$out"; then
      cov_ok=0; missing="$missing $(basename "$f"):no-verdict"
    fi
  done
  shopt -u nullglob
  if [ "$cov_ok" -eq 1 ]; then
    n="$(ls theory/sympy_checks/check_*.py 2>/dev/null | wc -l | tr -d ' ')"
    pass "30. all $n derivation checks have a recorded verdict"
  else
    bad "30. derivation-check coverage:$missing"
  fi
else
  skip "30. theory/sympy_checks not present"
fi

# 31. Every external-match claim in a check output has a PROVENANCE_AUDIT row.
#     A script may only claim agreement with a published value if that value's
#     page or equation is recorded. The screened phrases are the ones the sweep
#     in Session L3-PATCH found: an unattributed "published" is the failure mode.
prov="theory/PROVENANCE_AUDIT.md"
if [ -d theory/sympy_checks/output ]; then
  if [ ! -f "$prov" ]; then
    bad "31. $prov missing"
  else
    prov_ok=1; why31=""
    shopt -s nullglob
    for out in theory/sympy_checks/output/*.txt; do
      base="$(basename "$out" .txt)"
      # Does this output claim agreement with something external?
      if grep -qiE 'published|HBA[0-9]|p\.[0-9]{3,}|et al\. \([0-9]{4}\)' "$out"; then
        grep -q "$base" "$prov" || { prov_ok=0; why31="$why31 $base:no-row"; }
      fi
      # An unattributed "published" with no page or source is never acceptable.
      if grep -qiE 'published' "$out" && ! grep -qiE 'p\.[0-9]|Eq\.|source:' "$out"; then
        prov_ok=0; why31="$why31 $base:unattributed-published"
      fi
    done
    shopt -u nullglob
    if [ "$prov_ok" -eq 1 ]; then
      pass "31. every external-match claim is grounded in PROVENANCE_AUDIT.md"
    else
      bad "31. provenance gap:$why31"
    fi
  fi
else
  skip "31. theory/sympy_checks/output not present"
fi

# 32. Every PDF in docs/literature/ is named in the README index. A filename
#     that misrepresents its paper is how Session L3 came to cite the wrong
#     Heifetz year, so the index and the directory must agree exactly.
litdir="docs/literature"
if [ -d "$litdir" ]; then
  lit_ok=1; why32=""
  shopt -s nullglob
  for f in "$litdir"/*.pdf; do
    b="$(basename "$f")"
    grep -qF "\`$b\`" "$litdir/README.md" 2>/dev/null || { lit_ok=0; why32="$why32 $b:not-indexed"; }
  done
  shopt -u nullglob
  # Filenames known to have misrepresented their contents must not reappear.
  for stale in "haurwitz_1940_motion_of_atmospheric_disturbances.pdf" \
               "heifetz_2004_counter_propagating_rossby_waves.pdf"; do
    [ -f "$litdir/$stale" ] && { lit_ok=0; why32="$why32 $stale:corrected-name-reverted"; }
  done
  if [ "$lit_ok" -eq 1 ]; then
    n="$(ls "$litdir"/*.pdf 2>/dev/null | wc -l | tr -d ' ')"
    pass "32. all $n literature PDFs are indexed under their true identity"
  else
    bad "32. literature metadata:$why32"
  fi
else
  skip "32. docs/literature not present"
fi

# 33. Every judgement item in the derivation review carries a disposition.
#     None may sit in a bare "flagged" state waiting for someone to notice.
rev="theory/DERIVATION_REVIEW.md"
if [ -f "$rev" ]; then
  items=$(grep -cE '^\| \([a-j]\) \|' "$rev" || true)
  disp=$(grep -E '^\| \([a-j]\) \|' "$rev" | grep -cE 'Resolved|Accepted as a stated limitation' || true)
  if [ "$items" -eq 10 ] && [ "$disp" -eq 10 ]; then
    pass "33. all 10 review judgement items carry an explicit disposition"
  else
    bad "33. review dispositions: $disp of $items items dispositioned (want 10/10)"
  fi
else
  bad "33. $rev missing"
fi

# 34. The bibliography exists and carries at least 60 entries.
bib="manuscript/references.bib"
if [ -f "$bib" ]; then
  nbib="$(grep -cE '^@[a-zA-Z]+\{' "$bib")"
  if [ "$nbib" -ge 60 ]; then
    pass "34. references.bib has $nbib entries (>= 60)"
  else
    bad "34. references.bib has only $nbib entries (< 60)"
  fi
else
  bad "34. $bib missing"
fi

# 35. Every bibliography entry carries a resolvable identifier. A DOI normally;
#     a stable archive URL for the two Journal of Marine Research papers, which
#     predate DOI registration and are the origin of the result this paper tests.
if [ -f "$bib" ]; then
  gap="$(python3 - "$bib" <<'PY_EOF'
import re, sys
txt = open(sys.argv[1], encoding="utf-8").read()
bad = [k for k, b in re.findall(r"@\w+\{([^,]+),(.*?)\n\}", txt, re.S)
       if not re.search(r"\bdoi\s*=", b) and not re.search(r"\burl\s*=", b)]
print(" ".join(bad))
PY_EOF
)"
  if [ -z "$gap" ]; then
    pass "35. every references.bib entry has a doi (or archive url for pre-DOI)"
  else
    bad "35. bib entries with no identifier:$gap"
  fi
fi

# 36. Every \cite key in the manuscript drafts resolves to a bib entry.
if [ -f "$bib" ] && ls manuscript/drafts/*.tex >/dev/null 2>&1; then
  miss="$(python3 - "$bib" <<'PY_EOF'
import glob, re, sys
txt = open(sys.argv[1], encoding="utf-8").read()
keys = set(re.findall(r"@\w+\{([^,]+),", txt))
C = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
bad = set()
for f in glob.glob("manuscript/drafts/*.tex"):
    t = open(f, encoding="utf-8").read()
    for m in C.finditer(t):
        for k in m.group(1).split(","):
            k = k.strip()
            if k and k not in keys:
                bad.add(k)
print(" ".join(sorted(bad)))
PY_EOF
)"
  if [ -z "$miss" ]; then
    pass "36. every draft cite key resolves to a bib entry"
  else
    bad "36. unresolved cite keys:$miss"
  fi
else
  skip "36. no bibliography or no drafts yet"
fi

# 37. The gap statement and the dialectic challenge both exist, and the gap
#     statement references the challenge -- so the narrowed novelty claim cannot
#     be read without the evidence that narrowed it.
gs="docs/literature/GAP_STATEMENT.md"
dc="docs/literature/DIALECTIC_CHALLENGE.md"
if [ -f "$gs" ] && [ -f "$dc" ] && grep -q "DIALECTIC_CHALLENGE" "$gs"; then
  pass "37. gap statement and dialectic challenge exist and are cross-referenced"
else
  bad "37. gap statement / dialectic challenge missing or not cross-referenced"
fi

# 38. The literature review carries the exact sign-off closing statement.
lr="docs/literature/LITERATURE_REVIEW.md"
if [ -f "$lr" ] \
   && grep -q "THIS DOCUMENT REQUIRES OPERATOR SIGN-OFF BEFORE SESSION L11 MAY BEGIN" "$lr" \
   && grep -q "APPROVED BY THE OPERATOR" "$lr"; then
  pass "38. LITERATURE_REVIEW.md carries the sign-off closing statement"
else
  bad "38. LITERATURE_REVIEW.md missing or lacks the sign-off statement"
fi

echo "== $( [ "$fail" -eq 0 ] && echo "AUDIT PASSED" || echo "AUDIT FAILED ($fail check(s))" ) =="
exit "$fail"
