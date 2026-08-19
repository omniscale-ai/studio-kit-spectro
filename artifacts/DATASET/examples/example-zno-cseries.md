---
status: registered
date: 2026-08-19
---

# ZnO thin films by direct-write ALD — C-series (set C), impedance spectroscopy


<!-- toc -->

- [Instrument](#instrument)
- [Condition Axes](#condition-axes)
- [Sample Geometry](#sample-geometry)
- [Provenance](#provenance)

<!-- /toc -->

**ID**: `cpt-zno-dataset-cseries`
## Instrument

Gamry IFC1010, 20 mV rms, 0 V bias, 1.00 MHz → 9.97 Hz, 51 points. Gamry
`.DTA`, latin-1, decimal comma. Same instrument and trusted range as
`cpt-zno-dataset-750pass`: unusable above ~100 kHz, and above ~30 MΩ sample
impedance.

## Condition Axes

| axis | values | kind | note |
|---|---|---|---|
| deposition temperature | 150, 200, 250 °C | SYNTHESIS | ALD process temperature; different film per value |
| print speed | 5, 7.5, 10 mm/s | SYNTHESIS | different film per value |
| illumination | dark, UV, visible | MEASUREMENT | same film, three measurements |

All 27 spectra recorded in one session, 16/6/2026 15:03–16:29, at ambient
temperature; temperature channel at the ~1558 °C disconnected-sensor sentinel.

## Sample Geometry

Coplanar strips, ρ = R·w·d / L. **Fully recorded for this set**
(`ZnO -thickness-geometry-optical data.xlsx`), w = 0.395 mm throughout:

| deposition T | spacing L (mm) | thickness d (nm) | L/(w·d) (1/m) |
|---|---|---|---|
| 150 °C | 1.98 | 41.5 | 1.21×10⁸ |
| 200 °C | 1.68 | 77.2 | 5.5×10⁷ |
| 250 °C | 1.03 | 68.1 | 3.9×10⁷ |

**Both L and d vary systematically with the deposition-temperature axis.**
Across the full grid the geometric factor spans a factor **3.96**, against a
raw resistance trend of 9.4×. Any comparison along that axis is confounded
until geometry is divided out, and roughly a third of the apparent trend is
geometry alone.

## Provenance

`Electrical characterization- dynamic photocurrent, EIS/C-*-EIS-*.DTA`,
27 files, 16 June 2026. Set C of three nominally identical sets (A, B, C) grown
for reproducibility; only C has EIS. Companion: `cpt-zno-dataset-750pass`.
