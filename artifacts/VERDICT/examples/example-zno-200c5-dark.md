---
status: permitted
date: 2026-08-19
---

# Verdict — R_gb from ZnO 750-pass, 200 °C / 5.0 mm/s, dark


<!-- toc -->

- [Fit](#fit)
- [Evidence](#evidence)
- [Call](#call)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-verdict-750pass-200c5-dark`

## Fit

`cpt-zno-fit-750pass-200c5-dark`. Parameter judged: **R_gb** (7.307 MΩ).

## Evidence

| criterion | measured | threshold | licensed by |
|---|---|---|---|
| identifiability | arc closed: −Z″ falls to below half its apex at the lowest frequencies, and 2 points lie on the real axis | arc must turn over inside the window | `cpt-zno-calib-misfit-metric` |
| misfit | 6.6% over arc-bearing points | < 15% | `cpt-zno-calib-misfit-metric` |
| residual structure | systematic (2 runs over 16 arc points, z = −3.61) but misfit below the 10% gate | flagged only when misfit > 10% | `cpt-zno-calib-residual-structure` |
| noise | 4.2%, tier "clean" | < 35% unusable | `cpt-zno-calib-misfit-metric` |
| instrument range | \|Z\| max 7.4 MΩ, inside the 30 MΩ ceiling; 5 points above 100 kHz removed | 30 MΩ | `cpt-zno-calib-weight-floor` |

Independent corroboration: R_s + R_gb = 7.320 MΩ against a **directly measured**
R_dc of 7.394 MΩ (2 low-frequency points on the real axis) — 1.0% agreement on
a quantity the fit does not target.

## Call

**R_gb is usable**, 7.307 MΩ.

Recorded caveat: the residual is technically systematic (z = −3.61), meaning
this fit is not a perfect single arc. At 6.6% misfit it falls below the gate
that would call the parameter biased, and the calibration shows the runs test
alone carries a 35% false-positive rate on true single arcs — so this is
reported, not acted on. Were the misfit above 10% this verdict would refuse the
parameter as biased.

## Attestation

`eis_suite.verdict.usability` via `eis_suite.pipeline.analyze_spectrum`,
eis_suite @ 2026-08-19 on impedance 1.7.1+eis.1
(fork of ECSHackWeek/impedance.py @ 6a269c4), `python run_series.py 750pass`. Not hand-edited.
