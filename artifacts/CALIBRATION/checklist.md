# CALIBRATION — Review Checklist

- [ ] Is the scored quantity the one that actually matters for the use?
- [ ] Are the quantities it is blind to named?
- [ ] Are BOTH detection and false-positive rates reported?
- [ ] Is the scored rule the deployed rule (conjunction included), not just a
      component statistic?
- [ ] Is the ground truth independent of the tool's own regression suite?
- [ ] Is the inverse-crime exposure stated?
- [ ] Is the sweep actually informative, or flat across candidates?
- [ ] Can someone re-run this from the Attestation, seeds included?
- [ ] Was it scored on THIS system, at this scale, on this instrument? If not,
      is `basis: inherited` set and `inherited_from:` naming the source — and is everyone aware
      that no finding may be marked supported on it?
