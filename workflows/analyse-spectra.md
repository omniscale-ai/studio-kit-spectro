---
description: Invoke when the user asks to fit a model to a series of measurements and report parameters — e.g. "fit these impedance spectra", "get the crystallite sizes from these diffractograms", "process the new run, what are the resistances". Screens artefacts, fits, judges each fit, and emits FIT and VERDICT artifacts. Not tied to a technique or a model.
---

# Workflow: analyse-spectra

## Inputs

- A registered DATASET and the parameter(s) the user wants.

## Step 0 — Plan gate

Locate an `approved` ANALYSIS-PLAN covering this work. **If none exists, run
`workflows/plan-analysis.md` FIRST.** Changing a calibrated constant, adding
free parameters to the model, or excluding a condition group are interventions
that need to be in the plan; an unlisted one sends you back for an amendment.

## Steps

1. **Scan the series for artefacts, before fitting anything.** Run the scan
   across the whole series and record an ARTEFACT-SCAN. Series-level detection
   is not optional: a contaminant at a fixed position looks like an outlier in
   one measurement and is unmistakable across twenty, and per-measurement
   outlier rejection will remove real structure instead.

2. **Decide notch versus truncate, and score it.** Do not inherit the choice.
   Score both against a quantity neither is fitted to and record the numbers.

3. **Fit, and record a FIT per measurement — per direction, if the DATASET
   was acquired both ways.** The weighting must cite a CALIBRATION. Report
   effective sample size — if a handful of points carry the objective, the
   nominal point count is fiction. A both-ways acquisition is two
   measurements; fit both and let the plan's direction criterion judge their
   disagreement. Keeping one branch is a selection the protocol was designed
   to prevent.

4. **Judge each fit, and record a VERDICT.** The five criteria every model fit
   has — identifiability, misfit, residual structure, noise, instrument
   range — plus every criterion the ANALYSIS-PLAN declares under Verdict
   Criteria. Identifiability is not fit quality: if the feature determining a
   parameter never appeared in the measured range, the parameter is
   extrapolated however good the curve looks. **The identifiability test
   belongs to the model, and the verdict prints it**: pass it to
   `emit_artifacts.py --identifiability-test`. "The arc closes inside the
   window" is the right test for a single-arc impedance model and is not a
   test of anything else; a kit that assumed it would be a kit for one
   dataset.

4b. **Every threshold you judge against was scored on THIS system, or is
   declared borrowed.** A calibration from another system may not be cited
   (G3). To look at new data on another system's thresholds, write a
   CALIBRATION here with `basis: inherited` and `inherited_from:` naming the
   source; the verdicts
   are then provisional and no finding may be marked supported on them (G4).
   Re-score at this scale before claiming anything.

5. **Where a parameter is refused, say which kind of failure.** Imprecise
   (noise — widen the uncertainty) or biased (wrong model — no uncertainty
   covers it). The user's next action differs completely.

6. **Look at the figures.** Plot every fit against its data and look at them.
   Summary statistics have repeatedly passed fits that a glance would reject;
   if a curve does not pass through the points, no misfit number showing 2%
   overrides that.

7. **Gate.** `python3 {scripts}/graph_gate.py <artifacts-root>` must PASS.

## Hard rules

- NEVER report a parameter without its VERDICT.
- NEVER hand-edit a VERDICT. A verdict edited by the person who wants the
  parameter is not evidence.
- NEVER silently drop a measurement. Excluded measurements get a refusing
  verdict, so the exclusion is visible and countable.
- A parameter on a bound, or one whose determining feature lies outside the
  measured range, is NOT a measurement — regardless of the fit's residual.
- If a summary statistic disagrees with the figure, trust the figure and fix
  the statistic. Then calibrate the fix.
