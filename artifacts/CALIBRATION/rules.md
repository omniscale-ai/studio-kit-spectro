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

8. **Attest the library build, not just its version string.** A version number
   identifies a release; it does not identify the code that ran. This kit's own
   worked example was fitted with a *fork* of `impedance.py` whose
   `__version__` read `1.7.1` — the same string as the stock release it was
   not — carrying two extra modules and ~266 modified lines. For a month
   nothing said so, and anyone re-deriving these numbers from
   `pip install impedance==1.7.1` would have got different answers with no way
   to find out why. Name the fork and the commit:
   `impedance 1.7.1+atlant.1 (fork of ECSHackWeek/impedance.py @ 6a269c4)`.
   G7 checks an Attestation exists; only you can make it true.
