---
status: complete
date: 2026-08-19
---

# Single-arc fit — ZnO C-series, 250 °C / 5.0 mm/s, dark


<!-- toc -->

- [Measurement](#measurement)
- [Model](#model)
- [Weighting](#weighting)
- [Parameters](#parameters)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-fit-cseries-250c5-dark`
## Measurement

`C-250-5-EIS-DARK.DTA` from `cpt-zno-dataset-cseries`, after
`cpt-zno-scan-cseries`.

**35 of 51 points used.** Excluded: 5 mains-band, 14 physically impossible
(Z′ < 0 or −Z″ < 0, predominantly above 100 kHz). Retained
9.97 Hz – 100 kHz.

This measurement's |Z| reaches 141 MΩ, outside the 30 MΩ range the DATASET
declares trusted. It is fitted anyway so that its verdict can record the
failure with evidence rather than the measurement being dropped silently.

## Model

```
Z(ω) = R_s + 1 / ( 1/R_gb + Q·(jω)^α )
```

Four free parameters: R_s, R_gb, Q, α.

## Weighting

```
σ_i = sqrt( (0.02·|Z_i|)² + (0.002·p90|Z|)² ),   w_i = 1/σ_i
```

Licensed by `cpt-zno-calib-weight-floor`. Effective sample size 25.0 of 35.

## Parameters

| parameter | value | uncertainty | on bound? |
|---|---|---|---|
| R_s | 443 kΩ | — | no |
| R_gb | 82.2 MΩ | **undetermined** | no |
| Q | 4.229×10⁻¹² S·sᵅ | — | no |
| α | 0.965 | — | no |

R_gb is not on a numerical bound but is nonetheless undetermined: the arc never
turns over inside the window, so nothing in the data constrains where it would
close. Median relative deviation over arc-bearing points: **20.5%**. No
low-frequency point lies on the real axis, so R_dc cannot be measured
independently.

See `cpt-zno-verdict-cseries-250c5-dark` — this fit's parameters must not be
used.

## Attestation

`eis_suite.fit.fit_single_arc` via `eis_suite.pipeline.analyze_spectrum`,
eis_suite @ 2026-08-19 on impedance 1.7.1+atlant.1
(fork of ECSHackWeek/impedance.py @ 6a269c4), `python run_series.py cseries`.
