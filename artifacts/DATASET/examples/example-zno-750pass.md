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

**Electrode spacing L and width w were not recorded for this set.** Resistivity
and sheet resistance are therefore **unreportable** here; only thickness can be
divided out. The companion C-series does have full geometry, and there the
geometric factor L/(w·d) spans a factor 3.96 across the same nominal grid —
against a resistance trend of 9.4×.

## Provenance

`ZnO_750Pass_Data/EIS_750Pass/*.DTA`, 28 files. One
(`200C_10mms_Dark2_EIS.DTA`) contains 6 points from an interrupted sweep and is
excluded, leaving 27. Acquired 6 July 2026 in one session. Companion set:
`cpt-zno-dataset-cseries` (set C, same nominal grid, different coupons, full
electrode geometry).
