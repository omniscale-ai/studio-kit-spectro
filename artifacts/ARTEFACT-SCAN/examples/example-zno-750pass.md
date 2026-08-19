---
status: complete
date: 2026-08-19
---

# Artefact scan — ZnO 750-pass impedance set

**ID**: `cpt-zno-scan-750pass`

## Dataset

`cpt-zno-dataset-750pass`, 27 spectra × 51 points.

## Contaminations

| where | detected how | measurements affected | evidence |
|---|---|---|---|
| 49.87 Hz | series-level physicality | 70% | Z′ < 0 or −Z″ < 0 at exactly this frequency across the series |
| 62.92 Hz | series-level physicality | 63% | as above |
| 99.73 Hz | series-level physicality | 48% | second harmonic of the same source |
| 38.42 Hz | series-level physicality | worst-list | sideband of the same source |
| > 100 kHz | instrument range (DATASET) | all | scatter about the origin at \|Z\| ~ 10⁻⁴ of the arc, Z′ often < 0 |

The mains band is derived, not assumed: the detector tries 50 Hz and 60 Hz
supply frequencies with their harmonics and selects whichever explains the
observed spikes. It selected 50 Hz, band 39.7–99.8 Hz.

**The case that justifies series-level detection.** A mains-corrupted point
often retains Z′ > 0 and −Z″ > 0 — it passes every per-point physicality test
while being badly wrong. In one spectrum such points look like ordinary scatter;
across 27 they sit at identical frequencies in two-thirds of them. Per-spectrum
outlier rejection would have kept them and instead removed real curvature.

## Working Window

**Notch 38–100 Hz, retain 10–31 Hz.** Retained range 9.97 Hz – 100 kHz.

The alternative — truncating below 115 Hz — also discards 10–31 Hz, which is
the only data that says whether the arc closes, forcing every low-frequency
resistance to be an extrapolation. Both strategies were scored against R_dc
read directly off the low-frequency points, a target neither fit aims at:

| strategy | median \|deviation\| from measured R_dc | mean |
|---|---|---|
| notch 38–100 Hz, keep 10–31 Hz | **4.6%** | **6.4%** |
| truncate below 115 Hz | 16.9% | 29.3% |

Notching is closer in 17 of 20 spectra and makes R_dc directly measurable for
20 of 27, converting the main stated limitation of the truncating analysis into
a measured quantity.

Median 9 of 51 points removed per spectrum: 5 mains-band, 4 physically
impossible. No point is dropped without a named cause.

## Attestation

`eis_suite.artefacts.detect_mains` / `diagnose`, eis_suite @ 2026-08-19,
invoked via `python run_series.py 750pass`.
