---
status: complete
date: 2026-08-19
---

# Single-arc fit — ZnO 750-pass, 200 °C / 5.0 mm/s, dark


<!-- toc -->

- [Measurement](#measurement)
- [Model](#model)
- [Weighting](#weighting)
- [Parameters](#parameters)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-fit-750pass-200c5-dark`
## Measurement

`200C_5mms_Dark_EIS.DTA` from `cpt-zno-dataset-750pass`, after
`cpt-zno-scan-750pass`.

**42 of 51 points used.** Excluded: 5 mains-band (38–100 Hz), 5 physically
impossible (Z′ < 0 or −Z″ < 0, all above 100 kHz). Retained window
9.97 Hz – 100 kHz.

## Model

One depressed arc in series with a resistance:

```
Z(ω) = R_s + 1 / ( 1/R_gb + Q·(jω)^α )
```

Four free parameters: R_s, R_gb, Q, α. The CPE exponent α is free in
[0.20, 1.00]; α = 1 (an ideal arc) is a legitimate answer, not an artefact,
so the upper bound is inclusive.

## Weighting

Proportional noise with an absolute floor:

```
σ_i = sqrt( (rel·|Z_i|)² + (abs_frac·p90|Z|)² ),   w_i = 1/σ_i
rel = 0.02,  abs_frac = 0.002
```

Licensed by `cpt-zno-calib-weight-floor`.

Effective sample size (Kish) **28.1 of 42 points used**. Pure modulus weighting
(`w = 1/|Z|`) on this data collapses n_eff to 5–10 of 51 and drives α onto its
bound; the floor is what prevents that, and its size is what the calibration
determines.

## Parameters

| parameter | value | uncertainty | on bound? |
|---|---|---|---|
| R_s | 13.05 kΩ | — | no |
| R_gb | 7.307 MΩ | ±0.9% vs measured R_dc | no |
| Q | 9.688×10⁻¹¹ S·sᵅ | — | no |
| α | 0.938 | — | no |
| τ = (R·Q)^(1/α) | 0.439 ms | — | — |

Median relative deviation over arc-bearing points: **6.6%**.
R_s + R_gb = 7.320 MΩ against a directly measured R_dc of 7.394 MΩ — agreement
to 1.0%, on a quantity the fit does not target.

## Attestation

`eis_suite.fit.fit_single_arc` via `eis_suite.pipeline.analyze_spectrum`,
eis_suite @ 2026-08-19 on impedance 1.7.1+atlant.1
(fork of ECSHackWeek/impedance.py @ 6a269c4), `python run_series.py 750pass`.
