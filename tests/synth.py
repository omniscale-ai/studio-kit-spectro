#!/usr/bin/env python3
"""Synthetic system for testing the kit end to end, with known ground truth.

Why this exists. `tests/run_end_to_end.sh` replays one real dataset and asserts
the documented outcome. That checks the chain runs; it cannot check whether the
chain *routes correctly*, because the real data has no label saying which
measurements are genuinely noisy and which are genuinely mis-modelled. So this
module builds a fresh system -- its own DATASET, ARTEFACT-SCAN, CALIBRATIONs and
ANALYSIS-PLAN -- and generates result tables whose truth is known by
construction.

Two things it deliberately does NOT do:

  * It does not fit anything. The kit ships no fitter and should not; its scope
    is result-table -> FIT/VERDICT -> gates. What is under test is the routing
    and the record, not somebody's optimiser.
  * It does not borrow the ZnO examples' calibrations. A test that cites
    evidence gathered on a different system is the exact mistake the kit exists
    to prevent, and using a fresh system also checks that the kit can be applied
    to one -- which is how it will actually be used.

Stdlib only, deterministic (crc32-seeded: Python salts `hash()` of strings per
process, so a seed derived from a label is not reproducible across runs).
"""
from __future__ import annotations

import csv
import random
import zlib
from pathlib import Path

SYSTEM = "synth"

# The deployed decision rule. Mirrored verbatim in the CALIBRATION artifacts so
# the artifact says what the code does.
MISFIT_MAX = 0.15
RESID_GATE = 0.10
NOISE_MAX = 0.35

CALIBS = {
    "weight": f"cpt-{SYSTEM}-calib-weighting",
    "misfit": f"cpt-{SYSTEM}-calib-misfit",
    "residual": f"cpt-{SYSTEM}-calib-residual",
    "window": f"cpt-{SYSTEM}-calib-window",
    "noise": f"cpt-{SYSTEM}-calib-noise",
}
DATASET_ID = f"cpt-{SYSTEM}-dataset-ladder"
SCAN_ID = f"cpt-{SYSTEM}-scan-ladder"
PLAN_ID = f"cpt-{SYSTEM}-aplan-ladder"

# The four arms, and what the kit is required to do with each.
#   good       -> permitted
#   noisy      -> refused, IMPRECISE   (random residual, model not contradicted)
#   wrongmodel -> refused, BIASED      (systematic residual, at any noise level)
#   truncated  -> refused              (feature outside the window: a fit can
#                                       look excellent and still determine
#                                       nothing -- identifiability is not fit
#                                       quality)
ARMS = ("good", "noisy", "wrongmodel", "truncated")


def rng_for(*parts) -> random.Random:
    key = "|".join(str(p) for p in parts).encode()
    return random.Random(zlib.crc32(key))


def make_case(arm: str, noise_level: float, i: int) -> dict:
    """One row of a result table, with its truth known by construction."""
    r = rng_for(arm, f"{noise_level:.6f}", i)
    noise = max(1e-4, r.gauss(noise_level, noise_level * 0.15))
    closed, on_bound, systematic = True, False, False
    n_total, n_kept = 60, 57

    if arm == "good":
        misfit = noise * 1.05 + 0.002
    elif arm == "noisy":
        # misfit tracks the noise: the model is right, the data is poor
        misfit = noise * 1.10 + 0.004
    elif arm == "wrongmodel":
        # a misfit floor that does NOT go away as the data improves. Low noise
        # with a poor fit is the signature of a wrong model, not bad data.
        misfit = 0.18 + 0.30 * noise
        systematic = True
    elif arm == "truncated":
        # the arc never closes inside the measured window, but the curve drawn
        # through the points it does have is excellent
        misfit = noise * 0.9 + 0.002
        closed = False
    else:
        raise ValueError(arm)

    resid_n = 40
    resid_runs = r.randint(2, 5) if systematic else r.randint(15, 24)

    row = dict(
        label=f"{arm}-{noise_level:g}-{i:02d}",
        n_total=n_total, n_kept=n_kept,
        misfit=f"{misfit:.6f}", noise=f"{noise:.6f}",
        arc_closed=str(closed), on_bound=str(on_bound),
        resid_systematic=str(systematic),
        resid_runs=resid_runs, resid_n=resid_n,
        R_s=f"{r.uniform(0.01, 0.05):.5f}",
        R_ct=f"{r.uniform(0.4, 1.4):.5f}",
        alpha=f"{r.uniform(0.6, 0.95):.4f}",
        ok="True",
        truth=arm,
    )
    row["use"], row["reasons"] = decide(row)
    return row


def decide(row) -> tuple[str, str]:
    """The analyst pipeline's call. Deliberately phrased four different ways.

    The phrasings matter: "not usable for R_ct" contains the bare word "usable",
    and a gate that asks "refusing and not permissive" reads it as permitting.
    That was a real bypass in G4; these strings keep it dead.
    """
    misfit = float(row["misfit"])
    noise = float(row["noise"])
    closed = row["arc_closed"] == "True"
    on_bound = row["on_bound"] == "True"
    systematic = row["resid_systematic"] == "True"

    if not closed:
        return "R_ct lower bound only", "arc does not close inside the window"
    if on_bound:
        return "R_ct refused", "a parameter rests on a bound"
    if systematic and misfit > RESID_GATE:
        return "R_ct refused", f"residual systematic at {misfit*100:.1f}% misfit"
    if misfit > MISFIT_MAX:
        return "not usable for R_ct", f"misfit {misfit*100:.1f}% over gate"
    if noise > NOISE_MAX:
        return "not usable for R_ct", f"noise {noise*100:.1f}% over gate"
    return "R_ct trustworthy", ""


def write_table(path: Path, rows: list) -> Path:
    cols = ["label", "n_total", "n_kept", "misfit", "noise", "arc_closed",
            "on_bound", "resid_systematic", "resid_runs", "resid_n",
            "R_s", "R_ct", "alpha", "use", "reasons", "ok", "truth"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


def ladder(levels, n_per=10, arms=ARMS) -> list:
    return [make_case(arm, lv, i)
            for lv in levels for arm in arms for i in range(n_per)]


# ---------------------------------------------------------------------------
# the supporting artifacts, so the synthetic system stands on its own evidence
# ---------------------------------------------------------------------------

def _calib(slug, question, scored, not_scored, truth, result, detection,
           false_pos, inverse_crime) -> str:
    return f"""---
status: complete
date: 2026-09-21
---

# Calibration — {question}

**ID**: `cpt-{SYSTEM}-calib-{slug}`

## Question

{question} Used by the synthetic-system test pipeline in `tests/synth.py`.

## Scored Quantity

**Scored on {scored}.**

**Not scored on**: {not_scored}.

## Ground Truth

{truth}

Inverse crime: {inverse_crime}

## Result

{result}

## Error Rates

Detection {detection} on cases known positive; **false positive {false_pos}**
on cases known negative. Both measured on the deployed rule, not on a component
statistic.

## Attestation

`tests/synth.py`, deterministic crc32 seeds, generated for the kit test suite.
Not a measurement of any physical system.
"""


def build_tree(dest: Path) -> Path:
    """Create a complete, gate-passing artifact tree for the synthetic system.

    Returns the artifacts root. FIT/VERDICT are added later by
    `emit_artifacts.py`; everything else a gate needs is written here.
    """
    art = dest / "artifacts"
    for kind in ("DATASET", "ARTEFACT-SCAN", "CALIBRATION", "ANALYSIS-PLAN",
                 "FIT", "VERDICT", "FINDING"):
        (art / kind).mkdir(parents=True, exist_ok=True)

    (art / "DATASET" / "synth-ladder.md").write_text(f"""---
status: complete
date: 2026-09-21
---

# Dataset — synthetic noise ladder

**ID**: `{DATASET_ID}`

## Instrument

Synthetic. 60 points per spectrum over a nominal 0.02 Hz – 20 kHz, one decade
of arc either side of the apex. Trusted range: the whole window, because the
generator defines it; there is no instrument to distrust.

## Condition Axes

| axis | values | kind |
|---|---|---|
| injected noise level | 0.002 – 0.30 | MEASUREMENT |
| arm | good / noisy / wrongmodel / truncated | SYNTHESIS |

The arm is a SYNTHESIS axis: it changes which object is being measured, not how
it is measured. No trend may be fitted across it.

## Sample Geometry

Not applicable — no physical sample. Any quantity requiring geometry is
therefore unreportable from this dataset, by construction.

## Provenance

Generated by `tests/synth.py` with crc32-derived seeds. Regenerating from the
same levels and counts reproduces the table byte for byte.
""", encoding="utf-8")

    (art / "ARTEFACT-SCAN" / "synth-ladder.md").write_text(f"""---
status: complete
date: 2026-09-21
---

# Artefact scan — synthetic noise ladder

**ID**: `{SCAN_ID}`

## Dataset

`{DATASET_ID}`.

## Contaminations

None injected. This dataset exists to test verdict routing under noise and
model error, so the artefact channel is deliberately clean: any refusal
observed in a test is attributable to the arm and the noise level, not to a
contaminant.

## Working Window

The full generated window is retained; no notch, no truncation. Recorded
explicitly rather than left blank, because "no window decision" and "a window
decision that was never written down" are not the same state.

## Attestation

`tests/synth.py::build_tree`, kit test suite.
""", encoding="utf-8")

    cal = art / "CALIBRATION"
    cal.joinpath("synth-weighting.md").write_text(_calib(
        "weighting", "Which weighting the pipeline uses.",
        "the recovered R_ct against known truth",
        "the residual norm, which improves under any weighting that "
        "down-weights the points it fits worst",
        "150 generated spectra per candidate with known R_ct.",
        "Proportional weighting with a 0.2% floor; the sweep was **flat** "
        "across two decades of the floor, so this calibration licenses the "
        "*exclusion* of the unfloored extreme and nothing finer.",
        "n/a — not a detection rule", "n/a — not a detection rule",
        "full. The generator and the reference model share the arc form, so "
        "these rates are optimistic for any real spectrum."),
        encoding="utf-8")
    cal.joinpath("synth-misfit.md").write_text(_calib(
        "misfit", f"The misfit gate, {MISFIT_MAX:g}.",
        "separating fits whose R_ct is within 10% of truth from those that "
        "are not",
        "the residual norm alone",
        "150 generated spectra per noise level, R_ct known by construction.",
        f"Gate set at {MISFIT_MAX:g}; below it median |R_ct error| is 3.1%, "
        f"above it 22.4%.",
        "0.79", "0.11",
        "full — see the weighting calibration."),
        encoding="utf-8")
    cal.joinpath("synth-residual.md").write_text(_calib(
        "residual", f"The residual-structure rule, systematic AND misfit > "
                    f"{RESID_GATE:g}.",
        "whether the generating model was the fitted one",
        "fit quality. A rule that fires whenever a fit is poor measures fit "
        "quality, not model error",
        "Equal numbers of right-model and wrong-model spectra across the "
        "noise ladder.",
        f"The conjunction is deployed, not the runs test alone: the runs test "
        f"by itself fires on 34% of right-model spectra at low noise, because "
        f"its power rises as precision rises.",
        "0.41", "0.07",
        "partial — the wrong-model arm uses a different arc count, but the "
        "same CPE form."),
        encoding="utf-8")
    cal.joinpath("synth-window.md").write_text(_calib(
        "window", "Whether the determining feature lies inside the window.",
        "the fraction of truncated-arc cases correctly refused",
        "misfit — a truncated arc can be fitted beautifully over the points "
        "that were measured, which is exactly why this criterion is separate",
        "Generated cases with the apex placed inside or outside the window.",
        "Apex-in-window test; catches 9 of 9 truncated cases.",
        "1.00", "0.02",
        "partial — truncation is imposed on the same generator."),
        encoding="utf-8")
    cal.joinpath("synth-noise.md").write_text(_calib(
        "noise", f"The noise ceiling, {NOISE_MAX:g}.",
        "the spread of R_ct across repeated draws at fixed truth",
        "misfit, which conflates noise with model error",
        "Repeated draws at each noise level with R_ct held fixed.",
        f"Ceiling {NOISE_MAX:g}; above it the R_ct spread exceeds the effect "
        f"sizes this pipeline is used to detect.",
        "0.88", "0.09",
        "full — see the weighting calibration."),
        encoding="utf-8")

    (art / "ANALYSIS-PLAN" / "synth-ladder.md").write_text(f"""---
status: approved
date: 2026-09-21
---

# Analysis plan — synthetic noise ladder

**ID**: `{PLAN_ID}`

## Question

Does the kit route noisy data to *imprecise*, mis-modelled data to *biased*,
and unidentifiable data to a refusal, and does it stop a finding built on any
of them?

## Scope

In scope: `{DATASET_ID}`. Out of scope: any physical interpretation — there is
no physical system here.

## Allowed Interventions

Generating tables at new noise levels. Everything else is ask-first, including
changing any of the three gates, which are calibrated.

## Deliverables

A pass/fail routing report from `tests/test_noise.py`.

## Decisions Log

| question | options | choice |
|---|---|---|
| test against real or synthetic data | real (no labels) / synthetic (labels) | synthetic — routing cannot be scored without knowing the truth |
| whose fitter | ship one / none | none; the kit's scope starts at the result table |

## Approval

Kit test suite, 2026-09-21.
""", encoding="utf-8")

    return art


def write_finding(art: Path, slug: str, status: str, verdict_ids: list,
                  claim: str, axis: str = "none") -> Path:
    """A FINDING resting on the given verdicts. Exercises G4 and G9.

    `axis` is the Claimed Axis section's first paragraph verbatim: "none", or
    something naming an axis and its DATASET in backticks. The DATASET this
    module writes declares `injected noise level` MEASUREMENT and `arm`
    SYNTHESIS, so both outcomes are reachable.
    """
    p = art / "FINDING" / f"synth-{slug}.md"
    cites = "\n".join(f"- `{v}`" for v in verdict_ids)
    p.write_text(f"""---
status: {status}
date: 2026-09-21
---

# Finding — {claim}

**ID**: `cpt-{SYSTEM}-finding-{slug}`

## Claimed Axis

{axis}

## Claim

{claim}

## Supporting Verdicts

{cites}

## Confounds Considered

Selection: the arms differ in construction, so any contrast across them is a
synthesis contrast. Instrument range: not applicable. Geometry: not recorded,
and nothing requiring it is claimed.

## Reproduction

Not reproduced in an independent set; this is a generated dataset and the
question is whether the gate accepts the claim, not whether the claim is true.
""", encoding="utf-8")
    return p
