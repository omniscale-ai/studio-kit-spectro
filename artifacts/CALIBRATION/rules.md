# CALIBRATION — Generation & Validation Rules

1. **Score on the quantity you care about.** A constant tuned on one quantity
   is blind to errors in another. If a choice affects the shape of a fitted
   curve, scoring it on a scalar summary will not see the damage.
2. **Report both error rates.** Detection without a false-positive rate is not
   evidence. Enforced by `graph_gate.py` G3.
3. **Score the rule you deploy.** If the pipeline uses `A and B`, calibrate
   `A and B`. The false-positive rate of `A` alone may be several times worse,
   and reporting it as the rule's rate overstates the finding.
4. **Independence from the tool's own tests.** Where a library ships synthetic
   generators and expected answers, scoring on them measures reproduction of a
   regression suite. Use your own parameter grid, at your own scale, with your
   own corruptions.
5. **Name the inverse crime.** Say which conclusions are optimistic because the
   generator and the fitter share a model.
6. **A flat sweep licenses nothing.** If the scored quantity does not vary
   across candidates, this calibration cannot choose between them; say so
   rather than picking one and implying it was measured.
7. **Reproducible.** Seeds and invocation in Attestation. Enforced by G7.
