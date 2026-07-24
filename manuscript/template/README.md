# manuscript/template/

**Operator action.** Download the Springer Nature LaTeX bundle (v3.1, December
2024 or later) from the Springer Nature LaTeX author-support page and unpack it
into this directory. Do not transcribe it — fetch it (see the third-party-text
rule in `docs/CONVENTIONS.md`).

The unpacked bundle must contain, at minimum:

- `sn-jnl.cls` — the document class
- the eight `.bst` bibliography style files
- `sn-article.tex` — the reference article skeleton
- the Springer Nature user-manual PDF

Manuscript settings for this project:

- Document class line: `\documentclass[pdflatex,sn-mathphys-num]{sn-jnl}`
- All submission files must sit in a **single flat directory** (no subfolders).
- The `.bbl` is **pre-compiled** and submitted alongside the `.tex`.

This directory is intentionally empty until the bundle is unpacked; the download
is tracked as an outstanding action in `docs/SETUP_CHECKLIST.md`.
