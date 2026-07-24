"""House matplotlib style and figure provenance.

Defines the single visual style used by every figure in the project: a serif
font stack matching the manuscript, figure sizes in millimetres sized to
Springer Nature single- and double-column widths, colour-blind-safe colormaps
(a perceptually uniform sequential map, and a diverging map for signed vorticity),
consistent tick and spine treatment, and PDF output with fonts embedded as
Type 42 so the vector figures are editable and portable.

``provenance_sidecar`` writes the JSON record required by ``docs/CONVENTIONS.md``
next to each figure: the run IDs, processed-data files, config hashes and git
commit the figure was built from.

No figures are produced here; this module is imported by the figure scripts.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cmocean
import matplotlib as mpl

# --- Springer Nature column widths -----------------------------------------
SINGLE_COLUMN_MM = 88.0
DOUBLE_COLUMN_MM = 180.0
_MM_PER_INCH = 25.4

# --- colour-blind-safe colormaps -------------------------------------------
# Sequential (unsigned magnitudes) and diverging (signed vorticity). Both are
# perceptually uniform and remain legible in greyscale and to colour-vision
# deficiencies.
SEQUENTIAL_CMAP = cmocean.cm.thermal
DIVERGING_CMAP = cmocean.cm.balance


def mm_to_inch(mm: float) -> float:
    """Convert millimetres to inches (matplotlib's native figure unit)."""
    return mm / _MM_PER_INCH


def figure_size(width: str = "single", aspect: float = 0.72) -> tuple[float, float]:
    """Figure size in inches for a Springer column width.

    Parameters
    ----------
    width : {"single", "double"}
        Target column width.
    aspect : float
        Height / width ratio.
    """
    mm = {"single": SINGLE_COLUMN_MM, "double": DOUBLE_COLUMN_MM}[width]
    w = mm_to_inch(mm)
    return (w, w * aspect)


def apply_style() -> None:
    """Install the house style into matplotlib's global rcParams."""
    mpl.rcParams.update(
        {
            # serif stack matching the manuscript
            "font.family": "serif",
            "font.serif": [
                "Nimbus Roman",
                "Times New Roman",
                "Times",
                "STIXGeneral",
                "DejaVu Serif",
            ],
            "mathtext.fontset": "stix",
            # sizes tuned for a small journal figure
            "font.size": 8,
            "axes.titlesize": 8,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "figure.titlesize": 9,
            # ticks and spines
            "axes.linewidth": 0.6,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            # lines and colour cycle
            "lines.linewidth": 1.2,
            # cmocean registers its maps under a "cmo." prefix; the bare .name
            # ("thermal") is not a valid matplotlib colormap key.
            "image.cmap": f"cmo.{SEQUENTIAL_CMAP.name}",
            # vector PDF with embedded, editable Type 42 fonts
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
            "figure.dpi": 150,
        }
    )


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def provenance_sidecar(
    figure_path: str | Path,
    *,
    run_ids: Iterable[str],
    processed_files: Iterable[str],
    config_hashes: dict[str, str] | None = None,
    git_commit: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``<figure>.json`` recording how a figure was built.

    Returns the path to the sidecar written.
    """
    figure_path = Path(figure_path)
    sidecar = figure_path.with_suffix(figure_path.suffix + ".json")
    record = {
        "figure": figure_path.name,
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_ids": sorted(set(run_ids)),
        "processed_files": sorted(set(processed_files)),
        "config_hashes": dict(config_hashes or {}),
        "git_commit": git_commit if git_commit is not None else _git_commit(),
    }
    if extra:
        record["extra"] = extra
    sidecar.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return sidecar
