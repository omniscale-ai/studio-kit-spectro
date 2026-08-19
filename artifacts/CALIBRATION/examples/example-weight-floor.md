---
status: complete
date: 2026-08-19
---

# Calibration — absolute weight floor `abs_frac`

**ID**: `cpt-zno-calib-weight-floor`

## Question

The `abs_frac` term in `σ_i = sqrt((rel·|Z_i|)² + (abs_frac·p90|Z|)²)`, used by
`eis_suite.fit.make_weights` for every fit in this project. Previously 0.01.

## Scored Quantity

**Scored on the CPE exponent α**, against known truth.

**Not scored on**: R_dc alone — which is what the original calibration used, and
why it chose badly. R_dc error is nearly flat across two decades of this
parameter (3.0–8.8%), so scoring on it gives no reason to prefer any value. The
damage the floor causes is to *arc shape*, and a scalar resistance is blind to
shape.

This is the general failure: a constant tuned on quantity A while relied upon
for quantity B will be defensible on its own terms and wrong in use.

## Ground Truth

117 synthetic spectra from `bench_synth.py`: single depressed arcs plus
two-arc and Cole–Cole-distributed cases, at the ATLANT scale (MΩ arcs,
1 MHz–10 Hz, 51 points), with this lab's corruptions injected — 50 Hz mains,
high-frequency instrument garbage, low-frequency noise growth, window
truncation. Parameter grid and seeds chosen away from `impedance.py`'s own test
values, so this measures generalisation rather than reproduction of a
regression suite.

**Inverse crime, partial.** Single-arc cases are generated from the same CPE
form the fitter assumes, so single-arc *parameter recovery* is optimistic by
construction. The comparison *between* candidate floors is not affected — all
candidates fit the same generated data — which is what this calibration uses.

## Result

| abs_frac | α error med / p90 | R_dc error med / p90 | fits on a bound |
|---|---|---|---|
| 0.0 (pure modulus) | 0.062 / 0.227 | 8.8% / 22.2% | **20 of 117** |
| 0.0005 | 0.028 / 0.121 | 5.2% / 16.0% | 4 |
| 0.001 | 0.035 / 0.108 | 3.9% / 13.8% | 5 |
| **0.002 (chosen)** | **0.030 / 0.132** | 3.5% / 12.6% | 4 |
| 0.01 (previous) | 0.045 / 0.200 | 3.0% / 11.8% | 3 |

Chosen by the pre-registered criterion (median α error + median R_dc error).
Pure modulus is not the answer either: it puts 20 of 117 fits on a parameter
bound, the failure the floor was introduced to prevent.

Effect on the real spectrum that exposed the problem (750-pass 250 °C /
5.0 mm/s, visible): α 0.755 → 0.930, misfit 16.4% → 6.4%, R_gb within 4% of a
directly measured R_dc — where stock `impedance.py` had been fitting the rising
branch **better** than this pipeline.

End-to-end trade: α error 0.035 → 0.024 median, R_dc p90 6.8% → 9.0%. Not a
free win; the α gain was judged worth the R_dc cost because arc shape was what
was visibly broken.

## Error Rates

Not a detection rule, so detection/false-positive framing applies only to the
downstream consequence: with `abs_frac = 0.002`, fits landing on a parameter
bound (a false claim of determination) occur in 4 of 117 cases; at 0.0 the
**false-positive rate for "parameter determined"** is 20 of 117 = 17%.

## Attestation

`exp_floor_calibration.py`, eis_suite @ 2026-08-19, seeds from
`bench_synth.build_cases()` (deterministic, 0–2 per grid point).
