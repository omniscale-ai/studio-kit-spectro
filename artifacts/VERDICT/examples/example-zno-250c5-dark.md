---
status: refused
date: 2026-08-19
---

# Verdict — R_gb from ZnO C-series, 250 °C / 5.0 mm/s, dark


<!-- toc -->

- [Fit](#fit)
- [Evidence](#evidence)
- [Call](#call)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-verdict-cseries-250c5-dark`
## Fit

`cpt-zno-fit-cseries-250c5-dark`. Parameter judged: **R_gb** (nominally
82.2 MΩ).

## Evidence

| criterion | measured | threshold | licensed by |
|---|---|---|---|
| identifiability | **arc does not close** — −Z″ never returns toward the axis; no low-frequency point is on it | arc must turn over inside the window | `cpt-zno-calib-misfit-metric` |
| misfit | **20.5%** over arc-bearing points | < 15% | `cpt-zno-calib-misfit-metric` |
| residual structure | random (7 runs over 16 arc points, z = 0.00) | systematic if z < −2 and misfit > 10% | `cpt-zno-calib-residual-structure` |
| noise | 9.0%, tier "usable" | < 35% unusable | `cpt-zno-calib-misfit-metric` |
| instrument range | **\|Z\| reaches 141 MΩ, far outside the 30 MΩ ceiling**; 0.14 nA at 20 mV | 30 MΩ | `cpt-zno-calib-weight-floor` |

## Call

**R_gb is refused.** The nominal 82.2 MΩ is an unconstrained fit output, not a
measurement.

The parameter is **imprecise, not biased**. The residual is random (z = 0.00),
so the single-arc model is not being contradicted by the data's shape — there
simply is not enough signal to determine an arc. This distinction is the
actionable one: no reanalysis will fix it, and no better model will either.
The fix is instrumental — at 20 mV a 141 MΩ sample draws 0.14 nA, and 200 mV
would give ten times the current at the same impedance.

Contrast `cpt-zno-verdict-750pass-200c5-dark`, where a comparable misfit with a
*systematic* residual would have meant the opposite: a wrong model, unfixable by
better signal.

## Attestation

`eis_suite.verdict.usability` via `eis_suite.pipeline.analyze_spectrum`,
eis_suite @ 2026-08-19, `python run_series.py cseries`. Not hand-edited.
