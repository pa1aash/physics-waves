"""Conceptual schematics for the theory section (F1 and F2).

Two figures, both generated programmatically through ``src/figures/style.py`` so
they are reproducible in exactly the same way every later data figure is, and so
they carry the same house typography and the same provenance sidecar.

**F1 -- the beta-mechanism cartoon** (visual anchor for section 5). A chain of
fluid columns on the sphere is displaced meridionally. Conservation of potential
vorticity forces each displaced column to acquire relative vorticity of the
opposite sign to its displacement; the circulation that response induces is a
quarter wavelength out of phase with the displacement, and that quadrature is
what translates the pattern westward rather than growing it in place. The figure
is meant to be legible on its own to a reader who has not yet worked through the
derivation.

**F2 -- the counter-propagating Rossby wave schematic** (visual anchor for
section 10). Two potential-vorticity interfaces with oppositely signed jumps,
each carrying the F1 mechanism restricted to its own line, so each edge wave
propagates against its local mean flow. When the coupling across the jet can hold
them at a fixed relative phase, each wave's meridional velocity reinforces the
other's anomalies and the pair grows.

Run: ``python theory/figures/make_schematics.py``
Writes ``F1_beta_mechanism.pdf`` and ``F2_counter_propagating_waves.pdf``
alongside this script, each with its provenance sidecar.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.figures.style import (  # noqa: E402
    apply_style,
    figure_size,
    provenance_sidecar,
)

HERE = Path(__file__).resolve().parent

# Colour-blind-safe pair for the two signs of a vorticity or PV anomaly, chosen
# to match the diverging map used for signed fields in the data figures: cool for
# negative (anticyclonic in the northern hemisphere), warm for positive.
NEG = "#2c6f9b"
POS = "#b5482c"
GREY = "#555555"


def _curved_arrow(ax, xy, radius, sign, colour, lw=1.1):
    """Draw a circular arrow indicating the sense of rotation.

    ``sign > 0`` draws anticlockwise (cyclonic in the northern hemisphere),
    ``sign < 0`` clockwise (anticyclonic).
    """
    x0, y0 = xy
    t = np.linspace(0.35 * np.pi, 1.9 * np.pi, 120)
    if sign < 0:
        t = t[::-1]
    x = x0 + radius * np.cos(t)
    y = y0 + radius * np.sin(t)
    ax.plot(x, y, color=colour, lw=lw, solid_capstyle="round", zorder=3)
    ax.add_patch(
        FancyArrowPatch(
            (x[-2], y[-2]),
            (x[-1], y[-1]),
            arrowstyle="-|>",
            mutation_scale=7,
            color=colour,
            lw=lw,
            zorder=3,
        )
    )


# =============================================================================
# F1 -- the beta mechanism
# =============================================================================


def make_f1(path: Path) -> Path:
    """Two stacked panels: the vorticity response, then what it does."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figure_size("double", aspect=0.66), sharex=True)
    fig.subplots_adjust(hspace=0.42, left=0.10, right=0.97, top=0.90, bottom=0.03)

    x = np.linspace(0, 4 * np.pi, 800)
    eta = np.sin(x)

    # ---- panel (a): displacement and the vorticity it forces ---------------
    ax1.axhline(0.0, color=GREY, lw=0.8, ls=(0, (5, 3)), zorder=1)
    ax1.plot(x, eta, color="black", lw=1.6, zorder=2)

    for centre, sign in (
        (np.pi / 2, -1),
        (5 * np.pi / 2, -1),
        (3 * np.pi / 2, +1),
        (7 * np.pi / 2, +1),
    ):
        colour = NEG if sign < 0 else POS
        _curved_arrow(ax1, (centre, np.sin(centre)), 0.26, sign, colour)

    ax1.annotate(
        "poleward: $f$ rises, so $\\zeta$ must fall\n(anticyclonic response)",
        xy=(np.pi / 2 + 0.30, 1.02),
        xytext=(np.pi / 2 + 1.15, 2.30),
        fontsize=7,
        color=NEG,
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", lw=0.6, color=NEG, shrinkA=2, shrinkB=4),
    )
    ax1.annotate(
        "equatorward: $f$ falls, so $\\zeta$ must rise\n(cyclonic response)",
        xy=(3 * np.pi / 2 + 0.30, -1.02),
        xytext=(3 * np.pi / 2 + 1.15, -2.30),
        fontsize=7,
        color=POS,
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", lw=0.6, color=POS, shrinkA=2, shrinkB=4),
    )

    # Background PV gradient, in the left margin.
    ax1.annotate(
        "",
        xy=(-1.55, 2.5),
        xytext=(-1.55, -2.5),
        arrowprops=dict(arrowstyle="-|>", lw=1.0, color=GREY),
        annotation_clip=False,
    )
    ax1.text(
        -2.05,
        0.0,
        "background $\\bar q$ increases poleward",
        rotation=90,
        va="center",
        ha="center",
        color=GREY,
        fontsize=7,
    )

    ax1.set_xlim(-2.4, 4.35 * np.pi)
    ax1.set_ylim(-3.0, 3.0)
    ax1.axis("off")
    ax1.set_title(
        "(a)  a displaced column must change its relative vorticity to conserve $q$",
        fontsize=8,
        pad=2,
        loc="left",
    )

    # ---- panel (b): the induced flow, and where it takes the pattern -------
    shift = 0.5 * np.pi
    ax2.axhline(0.0, color=GREY, lw=0.8, ls=(0, (5, 3)), zorder=1)
    ax2.plot(x, eta, color="black", lw=1.6, zorder=3, label="now")
    ax2.plot(
        x,
        np.sin(x + shift),
        color=GREY,
        lw=1.2,
        ls=(0, (5, 2.5)),
        zorder=2,
        label="a quarter period later",
    )

    # Inverting zeta' = -beta*eta for eta = eta0 sin(kx) gives
    # v' = (beta eta0 / k) cos(kx): northward at x = 0, 2pi, 4pi and southward
    # at x = pi, 3pi. Northward flow at a node just west of a crest is exactly
    # what rebuilds the crest one step west, which is the westward propagation.
    northward_nodes = (0.0, 2 * np.pi, 4 * np.pi)
    southward_nodes = (np.pi, 3 * np.pi)
    for centre in northward_nodes:
        ax2.add_patch(
            FancyArrowPatch(
                (centre, -0.42),
                (centre, 0.42),
                arrowstyle="-|>",
                mutation_scale=8,
                color="black",
                lw=1.0,
                zorder=4,
            )
        )
    for centre in southward_nodes:
        ax2.add_patch(
            FancyArrowPatch(
                (centre, 0.42),
                (centre, -0.42),
                arrowstyle="-|>",
                mutation_scale=8,
                color="black",
                lw=1.0,
                zorder=4,
            )
        )

    ax2.text(
        0.35 * np.pi,
        2.30,
        "the induced $v'$ (black arrows) sits a quarter wavelength from the "
        "displacement, and\n"
        "is northward just west of each crest, so the pattern is rebuilt one "
        "step west",
        fontsize=7,
        ha="left",
        va="center",
    )

    ax2.add_patch(
        FancyArrowPatch(
            (3.05 * np.pi, -2.45),
            (2.05 * np.pi, -2.45),
            arrowstyle="-|>",
            mutation_scale=12,
            color="black",
            lw=1.7,
        )
    )
    ax2.text(
        2.0 * np.pi,
        -2.45,
        "westward:  $c = -\\beta/k^{2} < 0$   ",
        fontsize=8.5,
        ha="right",
        va="center",
    )

    ax2.text(4.30 * np.pi, -1.42, "east", fontsize=7, color=GREY, va="center", ha="right")
    ax2.add_patch(
        FancyArrowPatch(
            (4.05 * np.pi, -1.70),
            (4.30 * np.pi, -1.70),
            arrowstyle="-|>",
            mutation_scale=8,
            color=GREY,
            lw=0.9,
        )
    )

    ax2.legend(
        loc="upper right", frameon=False, fontsize=7, bbox_to_anchor=(1.005, 1.16), handlelength=2.4
    )

    ax2.set_xlim(-2.4, 4.35 * np.pi)
    ax2.set_ylim(-3.0, 3.0)
    ax2.axis("off")
    ax2.set_title(
        "(b)  that response is in quadrature, and it carries the pattern west",
        fontsize=8,
        pad=2,
        loc="left",
    )

    fig.suptitle(
        "F1  The $\\beta$ mechanism: why a Rossby wave goes west",
        fontsize=9.5,
        y=0.985,
    )
    fig.savefig(path)
    plt.close(fig)
    return path


# =============================================================================
# F2 -- counter-propagating Rossby waves
# =============================================================================


def make_f2(path: Path) -> Path:
    fig, (axL, axR) = plt.subplots(
        1,
        2,
        figsize=figure_size("double", aspect=0.52),
        gridspec_kw={"width_ratios": [1.0, 2.05], "wspace": 0.06},
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.02)

    b = 1.0

    # ---- left panel: the base state ---------------------------------------
    y = np.linspace(-2.4, 2.4, 500)
    ubar = np.exp(-((y / (0.80 * b)) ** 2))
    axL.plot(ubar, y, color="black", lw=1.5)
    axL.axhline(+b, color=POS, lw=0.9, ls=(0, (4, 3)))
    axL.axhline(-b, color=NEG, lw=0.9, ls=(0, (4, 3)))
    axL.axvline(0.0, color=GREY, lw=0.6)

    axL.text(1.20, +b + 0.16, "$\\Delta_1 > 0$", color=POS, fontsize=8, ha="right", va="bottom")
    axL.text(1.20, -b - 0.16, "$\\Delta_2 < 0$", color=NEG, fontsize=8, ha="right", va="top")
    axL.text(1.06, 1.95, "$\\bar u(y)$", fontsize=8.5, ha="right", va="center")
    axL.text(
        0.55,
        -2.70,
        "two interfaces carrying\noppositely signed PV jumps",
        fontsize=7,
        ha="center",
        va="top",
        color=GREY,
    )
    axL.set_xlim(-0.12, 1.42)
    axL.set_ylim(-3.35, 2.60)
    axL.axis("off")
    axL.set_title("base state", fontsize=8.5, pad=2)

    # ---- right panel: the phase-locked pair -------------------------------
    x = np.linspace(0, 3.6 * np.pi, 800)
    amp = 0.30
    dphase = 0.55 * np.pi  # northern wave lies this far west
    eta_n = amp * np.sin(x + dphase)
    eta_s = amp * np.sin(x)

    axR.axhline(+b, color=POS, lw=0.8, ls=(0, (4, 3)), zorder=1)
    axR.axhline(-b, color=NEG, lw=0.8, ls=(0, (4, 3)), zorder=1)
    axR.plot(x, b + eta_n, color=POS, lw=1.6, zorder=4)
    axR.plot(x, -b + eta_s, color=NEG, lw=1.6, zorder=4)

    # Counter-propagation, in the clear bands above and below.
    axR.add_patch(
        FancyArrowPatch(
            (1.55 * np.pi, b + 0.72),
            (0.95 * np.pi, b + 0.72),
            arrowstyle="-|>",
            mutation_scale=9,
            color=POS,
            lw=1.3,
        )
    )
    axR.text(
        1.66 * np.pi,
        b + 0.72,
        "westward relative to its own mean flow",
        fontsize=7,
        color=POS,
        va="center",
        ha="left",
    )
    axR.add_patch(
        FancyArrowPatch(
            (0.95 * np.pi, -b - 0.72),
            (1.55 * np.pi, -b - 0.72),
            arrowstyle="-|>",
            mutation_scale=9,
            color=NEG,
            lw=1.3,
        )
    )
    axR.text(
        1.66 * np.pi,
        -b - 0.72,
        "eastward relative to its own mean flow",
        fontsize=7,
        color=NEG,
        va="center",
        ha="left",
    )

    # The phase relationship: guide lines from each wave's crest.
    crest_n = (np.pi / 2 - dphase) % (2 * np.pi)
    crest_s = np.pi / 2
    for xc, colour in ((crest_n, POS), (crest_s, NEG)):
        axR.plot(
            [xc, xc], [-b - 0.10, b + 0.10], color=colour, lw=0.7, ls=(0, (1.5, 1.8)), zorder=2
        )
    axR.annotate(
        "",
        xy=(crest_n, 0.0),
        xytext=(crest_s, 0.0),
        arrowprops=dict(arrowstyle="<|-|>", lw=1.0, color="black"),
    )
    axR.text(
        (crest_n + crest_s) / 2,
        0.14,
        "$\\Delta\\epsilon$",
        fontsize=8.5,
        ha="center",
        va="bottom",
    )
    axR.text(
        crest_s + 0.30,
        -0.22,
        "northern crest lies west of the southern one\n"
        "($0 < \\Delta\\epsilon < \\pi$): each wave amplifies the other",
        fontsize=7,
        ha="left",
        va="top",
    )

    # Cross-jet coupling, in the clear stretch to the right of the phase label.
    for xc, colour, up in ((2.95 * np.pi, POS, False), (3.30 * np.pi, NEG, True)):
        y0, y1 = (-b + 0.16, b - 0.16) if up else (b - 0.16, -b + 0.16)
        axR.add_patch(
            FancyArrowPatch(
                (xc, y0),
                (xc, y1),
                arrowstyle="-|>",
                mutation_scale=7,
                color=colour,
                lw=1.0,
                ls=(0, (2.5, 2)),
                zorder=3,
            )
        )
    axR.annotate(
        "coupling across the jet,\nattenuated by $e^{-2kb}$",
        xy=(3.12 * np.pi, 0.52),
        xytext=(3.12 * np.pi, 1.95),
        fontsize=6.8,
        ha="center",
        va="center",
        arrowprops=dict(arrowstyle="-", lw=0.6, color=GREY, shrinkA=3, shrinkB=3),
    )

    axR.text(
        1.8 * np.pi,
        -2.85,
        "Each wave alone would only propagate. Held at a fixed relative phase, "
        "each wave's\nmeridional velocity drives potential vorticity into the "
        "other's crests and troughs,\nand the pair grows exponentially.",
        fontsize=7,
        ha="center",
        va="top",
    )

    axR.set_xlim(-0.30, 3.62 * np.pi)
    axR.set_ylim(-3.35, 2.60)
    axR.axis("off")
    axR.set_title("phase-locked pair", fontsize=8.5, pad=2)

    fig.suptitle(
        "F2  Instability as two counter-propagating Rossby waves",
        fontsize=9.5,
        y=0.985,
    )
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> int:
    apply_style()

    figs = {
        "F1_beta_mechanism.pdf": make_f1,
        "F2_counter_propagating_waves.pdf": make_f2,
    }
    for name, fn in figs.items():
        path = HERE / name
        fn(path)
        provenance_sidecar(
            path,
            run_ids=[],
            processed_files=[],
            extra={
                "kind": "conceptual schematic",
                "source": "theory/figures/make_schematics.py",
                "data": "none -- schematic, drawn from the derivation only",
                "anchors": (
                    "section 5 (beta mechanism)"
                    if name.startswith("F1")
                    else "section 10 (counter-propagating Rossby waves)"
                ),
            },
        )
        print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
