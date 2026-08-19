# VERDICT — Generation & Validation Rules

1. **No parameter without a verdict.** A number leaving this pipeline carries
   its verdict or it does not leave.
2. **A permitting verdict speaks to every criterion.** Identifiability, misfit,
   residual structure, noise, instrument range. Silence on a criterion is not
   a pass. Enforced by `graph_gate.py` G1.
3. **Every threshold cites a CALIBRATION.** Enforced by G2.
4. **Identifiability is not fit quality.** If the feature that determines a
   parameter never appeared inside the measured range, the parameter is
   extrapolated however well the curve fits — and fitters disagree about it by
   orders of magnitude precisely because it is unconstrained.
5. **Biased and imprecise are different verdicts.** A refusing verdict must say
   which. Enforced by G1.
6. **Summary statistics must be checked against the failure they are meant to
   catch.** A misfit measure normalised by a global scale can be small while
   the curve passes through empty space; a per-point relative measure can be
   large on an excellent fit. Whichever is used, its CALIBRATION must show it
   separating good from bad on cases judged independently.
7. **Script-generated, never hand-edited.** Enforced by G7.
