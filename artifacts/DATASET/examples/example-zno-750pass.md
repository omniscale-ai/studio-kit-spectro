---
status: registered
date: 2026-08-19
---

# ZnO thin films by direct-write ALD — 750-pass set, impedance spectroscopy


<!-- toc -->

- [Instrument](#instrument)
- [Condition Axes](#condition-axes)
- [Sample Geometry](#sample-geometry)
- [Provenance](#provenance)

<!-- /toc -->

**ID**: `cpt-zno-dataset-750pass`
## Instrument

Gamry IFC1010 potentiostat. Excitation 20 mV rms, DC bias 0 V. Swept
1.00 MHz → 9.97 Hz, 51 logarithmically spaced points, 10 per decade.
Files are Gamry `.DTA`: ASCII despite the extension, latin-1, and written with
a **decimal comma** — a naive parse silently truncates the fractional part.

**Trusted range.** Two boundaries, both established from the data rather than
assumed:

- **Above ~100 kHz** the instrument returns points scattered about the origin at
  |Z| of order 10⁻⁴ of the arc, frequently with Z′ < 0. These are not noisy
  measurements; they are not measurements.
- **Above ~30 MΩ** sample impedance, fit quality degrades sharply and above
  100 MΩ nothing is recoverable. At 20 mV a 100 MΩ sample draws 0.2 nA. Binned
  across both ZnO sets: median misfit 7.5% at 3–10 MΩ, 17.3% at 30–100 MΩ,
  39.7% above 100 MΩ with 0 of 5 usable.

Samples in the 250 °C dark group sit outside the second boundary. The remedy is
excitation amplitude, not analysis.

## Condition Axes

| axis | values | kind | note |
|---|---|---|---|
| deposition temperature | 150, 200, 250 °C | SYNTHESIS | ALD process temperature; each value is a **different film** |
| print speed | 5, 7.5, 10 mm/s | SYNTHESIS | scan speed of the direct-write head; different film |
| illumination | dark, UV, visible | MEASUREMENT | the same film measured three ways |

The temperature axis is the one that matters here. All 27 spectra were recorded
in a single bench session (6/7/2026, 09:32–12:06) at ambient temperature, with
the potentiostat's temperature channel pinned at ~1558 °C — its
disconnected-sensor sentinel — and 0 V bias throughout. The workbook
`Thickness - 750 passe.xlsx` labels the column "Deposition Temperature (°C)".

Consequently **no rate law may be fitted along this axis**: R(T) = R₀·exp(Eₐ/kT)
across these labels compares three different films measured at one temperature.

## Sample Geometry

Coplanar strip contacts. Conversion is ρ = R·w·d / L, with L the electrode
spacing, w their width, d the film thickness.

Thickness is recorded (`Thickness - 750 passe.xlsx`): 32.5–38.6 nm at 150 °C,
53.4–55.9 nm at 200 °C, 69.4–73.2 nm at 250 °C — a factor 2.25 across the grid,
correlated with the deposition-temperature axis.

**Electrode spacing L = 1.05 mm, constant across the cohort.** Recorded in the
Gamry `NOTES` block of every file — "1.05mm gap" in all 28 EIS files,
"gap-1.05mm" in all 17 photocurrent files.

**Width w = 0.395 mm is stated, not recorded.** The experimentalist states the
line width is the same mask as the C-series. It appears in no file header. It
enters ρ linearly, so it scales every resistivity here and cancels from every
ratio across the grid. Unresolved: the 27 I–V files carry an unlabelled
two-line note, identical in each — `1,0217 mm` and `0,9229 mm`. If those are
gap and width rather than two measurements of the gap, w = 0.923 mm and every
resistivity from this set is low by 2.34×.

Because L is constant here, the geometric factor L/(w·d) varies **only through
thickness, 2.25×**. In the companion C-series L runs 1.03–2.34 mm and is
correlated with the deposition-temperature label, so its geometric factor spans
3.96× against a resistance trend of 9.4×. This set is the better one for a
materials comparison, not the worse one.

> **Corrected 2026-09-22.** This artifact previously read "Electrode spacing L
> and width w were not recorded for this set. Resistivity and sheet resistance
> are therefore **unreportable** here." That was wrong, and it stood for a
> month: the gap was in the file headers the whole time, in a block the reader
> parsed past. The claim was about the *dataset*, not about any fit, so no
> verdict or calibration could have caught it — which is the argument for
> DATASET being an artifact that someone reads, rather than a preamble.
> Caught by the experimentalist on review.

## Provenance

`ZnO_750Pass_Data/EIS_750Pass/*.DTA`, 28 files. One
(`200C_10mms_Dark2_EIS.DTA`) contains 6 points from an interrupted sweep and is
excluded, leaving 27. Acquired 6 July 2026 in one session. Companion set:
`cpt-zno-dataset-cseries` (set C, same nominal grid, different coupons, full
electrode geometry).
