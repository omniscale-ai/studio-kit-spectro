# FIT — Generation & Validation Rules

1. **The model is an equation.** Names hide free-parameter counts.
2. **Weighting is declared and licensed.** It must cite a CALIBRATION. An
   unlicensed weighting choice is the easiest place for a pipeline to acquire
   a bias nobody can later locate.
3. **Report effective sample size.** Where weights span orders of magnitude,
   the nominal point count is not what the objective hears.
4. **Parameters on a bound are flagged, never reported as measurements.**
5. **Fit the cleaned points; do not silently refit the rejected ones.** The
   points used must match the ARTEFACT-SCAN's working window, or the deviation
   must be stated.
6. **Script-generated.** Enforced by `graph_gate.py` G7.
