---
status: complete
date: 2026-08-19
---

# Artefact scan — ZnO C-series impedance set


<!-- toc -->

- [Dataset](#dataset)
- [Contaminations](#contaminations)
- [Working Window](#working-window)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-scan-cseries`
## Dataset

`cpt-zno-dataset-cseries`, 27 spectra × 51 points.

## Contaminations

| where | detected how | measurements affected | evidence |
|---|---|---|---|
| 49.87 Hz | series-level physicality | 68.2% | Z′ < 0 or −Z″ < 0 at this frequency across the series |
| 38.42 Hz | series-level physicality | 59.1% | as above |
| 99.73 Hz | series-level physicality | 54.5% | second harmonic |
| 62.92 Hz | series-level physicality | 40.9% | as above |
| > 100 kHz | instrument range (DATASET) | all | scatter about the origin, Z′ often < 0 |
| \|Z\| > 30 MΩ | instrument range (DATASET) | 250 °C dark group | 0.2 nA of signal at 20 mV; no arc present to fit |

Same 50 Hz supply and band as the 750-pass set, detected independently from
this data (39.7–99.8 Hz).

## Working Window

**Notch 38–100 Hz, retain 10–31 Hz**; retained 9.97 Hz – 100 kHz. Strategy and
scoring as in `cpt-zno-scan-750pass`.

Median 9 of 51 points removed per spectrum. The 250 °C dark coupons remain in
the set but their impedance exceeds the trusted range, which their verdicts
record rather than their fits hiding.

## Attestation

`eis_suite.artefacts.detect_mains` / `diagnose`, eis_suite @ 2026-08-19 on impedance 1.7.1+eis.1
(fork of ECSHackWeek/impedance.py @ 6a269c4),
`python run_series.py cseries`.
