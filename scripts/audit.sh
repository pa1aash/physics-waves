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
#     message is a pass; a Python traceback is not). `make verify` is excluded
#     here — it calls `make audit`, so running it inside this audit would recurse;
#     instead its script is syntax-checked, and its constituents (this audit,
#     pytest, the gate record) are each checked.
#
#     `make sweep` was a deliberate stub until Session L7a and this check used to
#     assert it said so. It is now implemented, so what is asserted instead is the
#     contract it actually has: no campaign named is a usage error, and a named
#     campaign plans without executing.
cmd29=1; why=""
if command -v make >/dev/null 2>&1; then
  for t in refcheck manuscript; do
    make "$t" >/tmp/pw_cmd29_$t.log 2>&1 || true
    grep -qiE 'Traceback \(most recent call last\)' /tmp/pw_cmd29_$t.log && { cmd29=0; why="$why $t:traceback"; }
  done
  make figure ARGS=--style-preview >/tmp/pw_cmd29_figure.log 2>&1 || true
  grep -qiE 'Traceback \(most recent call last\)' /tmp/pw_cmd29_figure.log && { cmd29=0; why="$why figure:traceback"; }
  if make sweep >/tmp/pw_cmd29_sweep.log 2>&1; then cmd29=0; why="$why sweep:no-campaign-exited-0"; fi
  grep -qi 'usage: make sweep' /tmp/pw_cmd29_sweep.log || { cmd29=0; why="$why sweep:no-usage"; }
  make sweep CAMPAIGN=phase_speed ARGS=--dry-run >/tmp/pw_cmd29_sweepdry.log 2>&1 \
    || { cmd29=0; why="$why sweep:dry-run-failed"; }
  grep -qiE 'Traceback \(most recent call last\)' /tmp/pw_cmd29_sweepdry.log && { cmd29=0; why="$why sweep:traceback"; }
  grep -q 'plan not written' /tmp/pw_cmd29_sweepdry.log || { cmd29=0; why="$why sweep:dry-run-wrote-a-plan"; }
  bash -n scripts/verify.sh 2>/dev/null || { cmd29=0; why="$why verify:syntax"; }
  bash -n scripts/run_mpi.sh 2>/dev/null || { cmd29=0; why="$why run_mpi:syntax"; }
  bash -n scripts/sync_pod.sh 2>/dev/null || { cmd29=0; why="$why sync_pod:syntax"; }
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

# 39. The divergent-stability decision memo exists and states an explicit
#     recommendation. A memo that surveys options without choosing one is not a
#     decision memo, so the check requires the words "Option A" or "Option B" to
#     appear under a recommendation heading.
dsd="docs/literature/DIVERGENT_STABILITY_DECISION.md"
if [ -f "$dsd" ]; then
  # Must SELECT one option, not merely mention both. A survey of alternatives is
  # not a decision memo, and the first version of this check accepted one.
  rec="$(grep -oiE '(take|recommend|recommendation is|choose|adopt)[^.]{0,24}option [AB]' "$dsd" | head -1)"
  if [ -n "$rec" ]; then
    pass "39. divergent-stability decision memo selects an option ($rec)"
  else
    bad "39. $dsd has no explicit Option A / Option B recommendation"
  fi
else
  bad "39. $dsd missing"
fi

# 40. Every paper Session L4b targeted has an up-to-date status line in
#     MISSING.md -- obtained, or recorded as still missing with a reason. A
#     targeted acquisition attempt that leaves the record unchanged is how a
#     stale "unobtainable" note survives past the point where it is true.
miss="docs/literature/MISSING.md"
if [ -f "$miss" ]; then
  m40=1; why40=""
  for token in "10.1017/S0022112083000270" "10.1017/S0022112087002982" \
               "ABSTRACT-VERIFIED" "kasahara_1976_normal_modes_ultralong_waves.pdf"; do
    grep -qF "$token" "$miss" || { m40=0; why40="$why40 [$token]"; }
  done
  # Kasahara was obtained in L4: its row must no longer claim it is unavailable.
  if grep -qE 'kasahara.*(could not be obtained|not obtained|unobtainable)' "$miss"; then
    m40=0; why40="$why40 [kasahara-still-marked-missing]"
  fi
  if [ "$m40" -eq 1 ]; then
    pass "40. MISSING.md reflects the L4/L4b acquisition outcomes"
  else
    bad "40. MISSING.md stale for:$why40"
  fi
else
  bad "40. $miss missing"
fi

# 41. The stability EVP is not described as a sufficient stability test.
#     A normal-mode EVP cannot establish stability -- the operator is non-normal.
#     The word "sufficient" legitimately appears elsewhere (Ripa's conditions
#     genuinely ARE sufficient; section 8's criterion is "necessary, not
#     sufficient"), so this screens for the specific dangerous assertions and
#     also requires the section-9 caveat to still be present.
tex="theory/derivations.tex"
if [ -f "$tex" ]; then
  bad41=""
  # (a) dangerous phrasings, in any form that asserts it of THIS project's EVP.
  if grep -qiE '(genuine|actual|is a) sufficient (computational )?(test|condition)' "$tex"; then
    hits="$(grep -niE '(genuine|actual|is a) sufficient (computational )?(test|condition)' "$tex" \
            | grep -viE 'not a sufficient' | cut -d: -f1 | tr '\n' ' ')"
    [ -n "$hits" ] && bad41="$bad41 asserted-at-line:$hits"
  fi
  # (b) the caveat must still be there.
  grep -qF 'is \emph{not} a sufficient condition' "$tex" || bad41="$bad41 caveat-missing"
  grep -qi 'non-normal' "$tex" || bad41="$bad41 non-normality-note-missing"
  if [ -z "$bad41" ]; then
    pass "41. stability EVP scoped to modal instability; non-normality caveat present"
  else
    bad "41. section-9 scope regression:$bad41"
  fi
else
  bad "41. $tex missing"
fi

# 42. derivations.tex cites Ripa (1983) -- the divergent stability reference --
#     and does so inside the eigenvalue-problem section rather than only in the
#     bibliography.
if [ -f "$tex" ]; then
  if grep -q 'bibitem\[Ripa(1983)\]{ripa1983}' "$tex" \
     && grep -qE '\\cite[a-z]*\{[^}]*ripa1983' "$tex"; then
    pass "42. derivations.tex cites Ripa (1983) in the text and bibliography"
  else
    bad "42. derivations.tex does not cite Ripa (1983) in both text and bibliography"
  fi
fi

# 43. The unified provenance ledger covers every citation Session L4b examined.
prov="theory/PROVENANCE_AUDIT.md"
if [ -f "$prov" ]; then
  miss43=""
  for tok in "Ripa (1983)" "Hayashi & Young (1987)" "Skiba & Pérez-García (2004)" \
             "Skiba (2008)" "Skiba (2024)" "Constantin & Germain (2022)" \
             "Cao, Wang & Zuo (2023)" "Paldor, Shamir & Garfinkel (2020)" \
             "ABSTRACT-VERIFIED" "TITLE-ONLY"; do
    grep -qF "$tok" "$prov" || miss43="$miss43 [$tok]"
  done
  if [ -z "$miss43" ]; then
    pass "43. provenance ledger covers all L4b citations and both new categories"
  else
    bad "43. provenance ledger missing:$miss43"
  fi
else
  bad "43. $prov missing"
fi

# 44. The combined pre-L5 sign-off document carries its exact closing statement.
sig="docs/PRE_L5_SIGNOFF.md"
if [ -f "$sig" ] \
   && grep -q "THIS DOCUMENT REQUIRES OPERATOR SIGN-OFF BEFORE SESSION L5 MAY BEGIN." "$sig" \
   && grep -q "IT SUPERSEDES SEPARATE SIGN-OFF OF DERIVATION_REVIEW.MD, LITERATURE_REVIEW.MD," "$sig" \
   && grep -q "DERIVATIONS.TEX HAS BEEN RECONCILED TO MATCH THEM." "$sig"; then
  pass "44. PRE_L5_SIGNOFF.md carries the exact closing statement"
else
  bad "44. $sig missing or lacks the exact closing statement"
fi


# 45. No config still carries the Session-00 placeholder, and every config agrees
#     with the resolution policy in scripts/resolve_configs.py. A hand-edited
#     value that drifts from the policy is the failure mode this catches: the
#     config would still validate and still run, but the reason behind its
#     numbers would silently no longer be the reason recorded in the script.
if grep -rqF "TBD_SESSION_L5" configs/*/*.yaml 2>/dev/null; then
  bad "45. configs still carry the TBD_SESSION_L5 placeholder"
elif python scripts/resolve_configs.py --check >/dev/null 2>&1; then
  pass "45. every config resolved and consistent with the stated policy"
else
  bad "45. a config has drifted from resolve_configs.py's policy (make configs ARGS=--check)"
fi

# 46. The initial-condition dispatcher and the config schema name the same cases.
#     A mismatch is a config that validates and then fails at run time, which is
#     the most expensive place to find out.
check46='import sys, yaml; sys.path.insert(0, "."); from src.solver.initial_conditions import CONSTRUCTORS; schema = yaml.safe_load(open("configs/_schema.yaml")); sys.exit(0 if set(schema["properties"]["initial_condition"]["enum"]) == set(CONSTRUCTORS) else 1)'
if python -c "$check46" >/dev/null 2>&1; then
  pass "46. initial-condition dispatcher matches the schema enum"
else
  bad "46. initial-condition dispatcher and configs/_schema.yaml disagree"
fi

# 47. Every module in the solver core states the physics before the mechanism.
#     The project's standing rule is that a docstring says what the code is doing
#     physically before it says how; "Physics first." is the marker that the rule
#     was applied rather than assumed.
miss47=""
for f in src/solver/equations.py src/solver/harness.py \
         src/solver/evp_hough.py src/solver/evp_stability.py \
         src/solver/initial_conditions/common.py \
         src/solver/initial_conditions/williamson.py \
         src/solver/initial_conditions/galewsky.py \
         src/solver/initial_conditions/lauter.py \
         src/solver/initial_conditions/single_harmonic.py \
         src/solver/initial_conditions/jet_family.py; do
  if [ ! -f "$f" ]; then
    miss47="$miss47 [missing:$f]"
  elif ! grep -qF "Physics first" "$f"; then
    miss47="$miss47 [$f]"
  fi
done
if [ -z "$miss47" ]; then
  pass "47. every solver-core module states the physics before the mechanism"
else
  bad "47. solver-core modules without a physics-first docstring:$miss47"
fi

# 48. The nondivergent scope of the stability EVP, and its one-signed bias, are
#     stated in the module that produces the numbers -- not only in the decision
#     memo. A growth rate escaping into a figure without that qualification is
#     the specific failure Session L4b set out to prevent.
ev="src/solver/evp_stability.py"
if [ -f "$ev" ] \
   && grep -qF "NONDIVERGENT" "$ev" \
   && grep -qi "overestimat" "$ev" \
   && grep -qF "DIVERGENT_STABILITY_DECISION.md" "$ev" \
   && grep -qi "non-normal" "$ev"; then
  pass "48. stability EVP carries its scope, its bias direction and the decision reference"
else
  bad "48. $ev missing the nondivergent-scope / bias / non-normality statement"
fi


# 49. Every analysis-pipeline module built in Session L6 is genuinely implemented
#     -- no stub docstring left behind -- and states the physics before the
#     mechanism. The two modules that are deliberately still stubs are named
#     explicitly, so that finishing them later cannot be mistaken for a
#     regression and so that leaving them cannot be mistaken for an oversight.
miss49=""
for f in src/diagnostics/slices.py src/diagnostics/conservation.py \
         src/diagnostics/spectra.py src/analysis/compute_error_norms.py \
         src/analysis/extract_hovmoller.py src/analysis/fit_phase_speed.py \
         src/analysis/fit_growth_rate.py src/analysis/spectral_decompose.py \
         src/analysis/extract_structure.py src/analysis/hough.py \
         src/analysis/stability_evp.py; do
  if [ ! -f "$f" ]; then
    miss49="$miss49 [missing:$f]"
  elif grep -q "^# Implementation: Session" "$f"; then
    miss49="$miss49 [still-a-stub:$f]"
  elif ! grep -qF "Physics first" "$f"; then
    miss49="$miss49 [no-physics-first:$f]"
  fi
done
for f in src/analysis/process_reanalysis.py src/analysis/aggregate_results.py; do
  grep -q "^# Implementation: Session" "$f" 2>/dev/null \
    || miss49="$miss49 [expected-to-remain-a-stub:$f]"
done
if [ -z "$miss49" ]; then
  pass "49. analysis-pipeline modules implemented, physics-first; L8/L9 stubs still stubs"
else
  bad "49. analysis-pipeline module problems:$miss49"
fi

# 50. The synthetic-data fitter tests recover their known ground truth to better
#     than 0.1%, for every (m, omega) and every sigma case. This runs the tests
#     rather than trusting that they exist, and it also checks that the tolerance
#     constant itself has not been quietly relaxed -- a test that passes because
#     its bar was lowered is worse than no test.
if grep -q "^FITTER_TOLERANCE = 1e-3$" tests/test_analysis_pipeline.py; then
  if python -m pytest tests/test_analysis_pipeline.py -q \
       -k "recovers_known_input or superimposed_oscillation or conventions_differ" \
       >/dev/null 2>&1; then
    pass "50. every synthetic fitter case recovers ground truth to better than 0.1%"
  else
    bad "50. a synthetic fitter case fails to recover its known input to 0.1%"
  fi
else
  bad "50. FITTER_TOLERANCE is no longer 1e-3 in tests/test_analysis_pipeline.py"
fi

# 51. The Part-6 regression test still reproduces Session L5's (m=2, n=4) finding:
#     a measured slowing of 15.72% against a Hough eigenvalue of 15.77%, agreeing
#     to 0.05 percentage points. This is the session's headline cross-check and
#     the thing most likely to move silently if a fitter is refactored.
if [ -f runs/P-17/provenance.json ]; then
  if python -m pytest tests/test_analysis_pipeline.py -q \
       -k "hough_comparison_reproduces" >/dev/null 2>&1; then
    pass "51. Hough comparison still reproduces Session L5's (m=2,n=4) result"
  else
    bad "51. the measured-vs-Hough comparison no longer reproduces Session L5's result"
  fi
else
  skip "51. run P-17 not present; cannot check the Hough regression"
fi

# 52. The Part-7 regression test still reproduces Session L5's shear ladder --
#     all five rungs, each with its necessary verdict, sufficient verdict and
#     growth rate -- and the refined thresholds still lie inside the brackets
#     that session reported.
if python -m pytest tests/test_analysis_pipeline.py -q \
     -k "shear_ladder_reproduces or three_regimes or growth_onset_lies" >/dev/null 2>&1; then
  pass "52. shear ladder and thresholds still reproduce Session L5"
else
  bad "52. the stability sweep no longer reproduces Session L5's shear ladder"
fi

# 53. Output cadence scales with rotation rate, in both directions, and the
#     scaling actually defeats the aliasing failure Session L6 found. This is the
#     load-bearing check of Session L7a: an undersampled phase-speed run returns a
#     confident answer of the wrong magnitude AND the wrong sign, while every
#     indicator computable from its own output reads comfortable. The test
#     fabricates that wave and confirms the fit recovers the truth at the scaled
#     cadence and the alias at the stated one.
if python -m pytest tests/test_sweep_cadence.py -q \
     -k "scales_down or scales_up or holds_samples_per_period or unscaled_cadence_aliases or \
         naive_margin_indicator or scaled_cadence_recovers or no_planned_cadence" \
     >/dev/null 2>&1; then
  pass "53. cadence scales with Omega in both directions and defeats the alias"
else
  bad "53. the Omega-dependent cadence scaling no longer holds"
fi

# 54. The resume-on-failure path identifies an interrupted run from a fabricated
#     provenance record, without needing a real Dedalus run to die first. Session
#     L7a chose clean-restart-from-archive over checkpoint-resume (docs/COMPUTE.md,
#     "Resume on failure"), so what is checked is detection plus a non-destructive
#     archive, never state reconstruction.
if python -m pytest tests/test_resume_check.py -q \
     -k "failed_run_is_identified or killed_run_is_identified or archiving_moves or \
         archived_record_is_still_read_only or default_invocation_changes_nothing" \
     >/dev/null 2>&1; then
  pass "54. an incomplete run is detected and archived without losing anything"
else
  bad "54. resume_check no longer detects or safely archives an incomplete run"
fi

# 55. The pod sync's flags and exclusions are exercised against a throwaway local
#     directory standing in for the pod, with no pod reachable. runs/ is
#     gitignored, so this script is the only route run data has between machines,
#     and a wrong exclusion pattern does not fail -- it silently moves the wrong
#     thing, or silently omits the one file that mattered.
if python -m pytest tests/test_sync_pod.py -q \
     -k "dry_run_lists_the_expected_files or dry_run_excludes_caches or \
         real_pull_brings_the_run or refuses_to_overwrite or never_carries_run_output" \
     >/dev/null 2>&1; then
  pass "55. sync dry-run produces the expected file list against the local stand-in"
else
  bad "55. the pod sync no longer transfers the expected files, or lost its guards"
fi

# 56. The harness runs on more than one MPI rank. Every run recorded before
#     Session L7a was serial, and two bugs hid behind that: a rank-local area
#     average that raised IndexError on every rank but one, and every rank racing
#     to write the provenance record so the first set the read-only tripwire and
#     the next tripped it. Neither could produce a wrong number -- both aborted
#     before the physics started -- but both made the pod unusable.
if python -m pytest tests/test_mpi_harness.py -q >/dev/null 2>&1; then
  pass "56. the harness survives and agrees across MPI ranks"
else
  bad "56. the harness no longer runs correctly on more than one MPI rank"
fi

echo "== $( [ "$fail" -eq 0 ] && echo "AUDIT PASSED" || echo "AUDIT FAILED ($fail check(s))" ) =="
exit "$fail"
