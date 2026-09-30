# VERDICT — Generation & Validation Rules

1. **No parameter without a verdict.** A number leaving this pipeline carries
   its verdict or it does not leave.
2. **A permitting verdict speaks to every criterion.** Identifiability, misfit,
   residual structure, noise, instrument range — the five every model fit
   has — plus whatever the system's ANALYSIS-PLAN declares under Verdict
   Criteria. Silence on a criterion is not a pass. Enforced by
   `graph_gate.py` G1.
3. **Every threshold cites a CALIBRATION scored on this system.** Enforced by
   G2 (it resolves) and G3 (its scope includes this system). A calibration
   marked `inherited` licenses a provisional verdict and no supported finding.
4. **Identifiability is not fit quality.** If the feature that determines a
   parameter never appeared inside the measured range, the parameter is
   extrapolated however well the curve fits — and fitters disagree about it by
   orders of magnitude precisely because it is unconstrained. **The test is
   the model's, and the verdict names it**: "arc apex inside the window" for a
   single arc, "peak maximum and both half-maxima inside the scan" for a
   diffraction line. A verdict that says "identifiable" without saying what
   was tested has asserted, not judged.
5. **Biased and imprecise are different verdicts.** A refusing verdict must say
   which. Enforced by G1.
6. **Summary statistics must be checked against the failure they are meant to
   catch.** A misfit measure normalised by a global scale can be small while
   the curve passes through empty space; a per-point relative measure can be
   large on an excellent fit. Whichever is used, its CALIBRATION must show it
   separating good from bad on cases judged independently.
7. **Script-generated, never hand-edited.** Enforced by G7.
