---
description: Invoke when a threshold, constant or method choice needs justifying or changing — e.g. "what should the cutoff be", "this filter is too aggressive", "why is that value 0.01". Produces a CALIBRATION artifact scored against ground truth.
---

# Workflow: calibrate-threshold

## Inputs

- The constant, threshold or method choice in question, and where it is used.

## Step 0 — Plan gate

Changing a calibrated constant is ask-first unless the ANALYSIS-PLAN authorises
it. A constant that moves because a result looked wrong is no longer evidence.

## Steps

1. **Name the quantity that matters.** What does this constant affect that
   someone will rely on? That is what to score on. Scoring on a convenient
   scalar instead is the commonest way a pipeline acquires a defensible,
   invisible bias — a constant tuned on one quantity is blind to errors in
   another.

2. **Establish ground truth independently.** Build synthetic cases at your
   own scale with your own corruptions, or find an independent measurement.
   Where the tool ships its own synthetic tests with expected answers, do not
   score on those: that measures reproduction of a regression suite.

3. **Sweep, and record the whole sweep.** If the scored quantity is flat across
   candidates, this evidence licenses nothing — say so rather than picking a
   value and implying it was measured.

4. **Score the rule you will deploy.** If the pipeline uses `A and B`, calibrate
   `A and B`. A component statistic's error rates are not the deployed rule's,
   and can be several times worse.

5. **Report both error rates.** Detection and false-positive, on cases known to
   be negative. A rule that fires on everything detects everything.

6. **Name the inverse crime.** If the generator shares a model with the fitter,
   say which conclusions are flattered by it.

7. **Record the CALIBRATION** and update every artifact citing the old value.

8. **Gate.** `python3 {scripts}/graph_gate.py <artifacts-root>` must PASS.

## Hard rules

- NEVER change a constant without producing a CALIBRATION for the new value.
- NEVER report detection without false-positive rate.
- If the new value improves one quantity and degrades another, state the trade
  explicitly. Silent trades are how a pipeline drifts.
- A calibration that cannot separate good from bad on cases judged independently
  is not a calibration, however sophisticated its statistic.
