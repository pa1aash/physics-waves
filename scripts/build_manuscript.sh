#!/usr/bin/env bash
# make manuscript: compile the manuscript to PDF.
#
# Prefers manuscript/main.tex (the real submission, from Session L11). Until that
# exists, falls back to compiling theory/derivations.tex standalone and says so
# clearly. Reports compile success/failure and the output PDF path.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

if [ -f manuscript/main.tex ]; then
  target="manuscript/main.tex"; kind="manuscript"
elif [ -f theory/derivations.tex ]; then
  target="theory/derivations.tex"
  kind="FALLBACK (theory/derivations.tex; the real manuscript build arrives in Session L11)"
else
  echo "[manuscript] nothing to build: no manuscript/main.tex and no theory/derivations.tex."
  exit 1
fi

echo "[manuscript] building ${target} — ${kind}"

# A standalone document needs a \documentclass. Until the theory file is fleshed
# out (or manuscript/main.tex exists), there is genuinely nothing to compile.
if ! grep -q '\\documentclass' "${target}"; then
  echo "[manuscript] ${target} has no \\documentclass yet (it is a stub, populated in"
  echo "[manuscript] the theory workstream); nothing to compile. Not a failure."
  exit 0
fi

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "[manuscript] pdflatex not found; install a LaTeX distribution to compile. Not built."
  exit 1
fi

outdir="$(dirname "${target}")"
log=/tmp/pw_manuscript.log
if pdflatex -interaction=nonstopmode -halt-on-error -output-directory "${outdir}" "${target}" >"${log}" 2>&1; then
  pdf="${target%.tex}.pdf"
  echo "[manuscript] OK -> ${pdf}"
  exit 0
else
  echo "[manuscript] compile FAILED (see ${log}):"
  tail -n 8 "${log}"
  exit 1
fi
