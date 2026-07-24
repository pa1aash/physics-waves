"""Pipeline stage 11: final publication figure set (blueprint section 12).

The full figure pipeline — building each manuscript figure from aggregated run
results with a provenance sidecar — is implemented in Session L10. This module
currently provides only a ``--style-preview`` mode: it renders one small
synthetic placeholder plot (a decaying sine, nothing physical) in the house style
defined by ``src/figures/style.py`` so the visual language (fonts, colours,
sizing, PDF font embedding) can be sanity-checked now rather than nine sessions
from now.

Usage:
    python src/figures/make_figures.py --style-preview
    python src/figures/make_figures.py                # prints the stub notice
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PREVIEW = REPO / "figures" / "style_preview.png"


def style_preview() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # style.py lives beside this file; add its directory to the path so this works
    # whether run as a script or imported.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import style

    style.apply_style()
    fig, ax = plt.subplots(figsize=style.figure_size("single"))
    x = np.linspace(0, 4 * np.pi, 400)
    for k in (1, 2, 3):
        ax.plot(x, np.sin(k * x) / k, label=f"mode k={k}")
    ax.set_xlabel("x  (placeholder, not physical)")
    ax.set_ylabel("amplitude  (placeholder)")
    ax.set_title("House-style preview — synthetic, not a result")
    ax.legend()
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PREVIEW)
    plt.close(fig)
    print(f"[figure] house-style preview written: {PREVIEW.relative_to(REPO)}")
    print("[figure] check fonts, colours and sizing look as intended.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Figure pipeline (stub) / house-style preview.")
    ap.add_argument(
        "--style-preview", action="store_true", help="render a house-style preview and exit"
    )
    args = ap.parse_args(argv)

    if args.style_preview:
        return style_preview()

    print("[figure] the figure pipeline is implemented in Session L10 — not yet available.")
    print("[figure] run `make figure ARGS=--style-preview` to preview the house style now.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
