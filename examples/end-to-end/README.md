# End to end: what goes in, what happens, what comes out

A complete run of the kit on real data, from a scientist's result table to
gated artifacts. Everything below is reproducible from this repository —
`tests/run_end_to_end.sh` executes it and checks the result.

The point of reading this is not the ZnO physics. It is to see **what the kit
refuses, and why**, because that is the output that distinguishes it from a
fitting script.

---

## What was given

**The measurement.** 27 impedance spectra of ZnO thin films grown by
direct-write ALD, on a Gamry IFC1010: 1.00 MHz → 9.97 Hz, 51 logarithmically
spaced points, 20 mV rms, 0 V bias. Three deposition temperatures × three print
speeds × three illumination conditions.

**What the scientist already had**, before any of this kit:

- the raw `.DTA` files
- a fitting pipeline that produced a result table — one row per spectrum, with
  the fitted circuit parameters (`R_s`, `R_gb`, `Q`, `alpha`), a misfit number,
  a noise estimate and some diagnostics

That table is shipped here as `tests/provenance/results_750pass.csv`. It is the
*only* input the kit needs; it is deliberately not tied to any one analysis
package.

**What was missing** — and this is the interesting part — was any statement of
which of those 27 sets of fitted parameters could actually be used. The table
has a number in every row. So does a table of nonsense.

---

## What was done

### 1. Register the dataset — before fitting anything

`artifacts/DATASET/examples/example-zno-750pass.md`

Two fields decide whether any later conclusion can exist, so the workflow
demands them up front:

- **Condition axes, each declared MEASUREMENT or SYNTHESIS.** Deposition
  temperature is a *synthesis* axis: each label is a different film, all
  measured at bench temperature in one session. Nothing in the data files says
  so — the instrument's temperature channel sits at its disconnected-sensor
  sentinel throughout.
- **The trusted instrument range.** Above ~100 kHz the instrument returns
  scatter about the origin; above ~30 MΩ sample impedance, a 20 mV excitation
  drives 0.2 nA and nothing is recoverable.

### 2. Scan the series for artefacts — not each spectrum separately

`artifacts/ARTEFACT-SCAN/examples/example-zno-750pass.md`

50 Hz mains pickup makes a point at 49.87 Hz physically impossible in 70% of
spectra. In any *single* spectrum those points look like ordinary scatter; only
across the series are they unmistakable. The band is derived from the data, not
hard-coded.

The scan also records the *strategy*: notch the band and keep 10–31 Hz, rather
than truncating the window. Scored against a target neither fit aims at
(directly measured R_dc): 4.6% vs 16.9% median deviation.

### 3. Generate FIT and VERDICT records from the table

```bash
python3 scripts/emit_artifacts.py tests/provenance/results_750pass.csv \
    --system zno \
    --dataset cpt-zno-dataset-750pass \
    --scan    cpt-zno-scan-750pass \
    --out artifacts \
    --model 'Z(w) = R_s + 1/(1/R_gb + Q (jw)^alpha)' \
    --weighting 'sigma_i = sqrt((0.02|Z_i|)^2 + (0.002 p90|Z|)^2)' \
    --weighting-calib cpt-zno-calib-weight-floor \
    --misfit-calib    cpt-zno-calib-misfit-metric \
    --residual-calib  cpt-zno-calib-residual-structure \
    --attest 'eis_suite @ 2026-08-19'
```

These are generated, never hand-written: a verdict edited by the person who
wants the parameter is not evidence.

### 4. Gate

```bash
python3 scripts/graph_gate.py artifacts     # 7 cross-artifact rules
python3 scripts/check_claims.py             # quoted numbers vs provenance
cfs validate                                # structure, ID grammar, TOC
```

---

## What comes out

### 27 FIT records and 27 VERDICT records

| | n |
|---|---|
| **permitted** — R_gb usable | **17** |
| refused as **biased** — the model is wrong, no uncertainty covers it | 7 |
| refused as **imprecise** — the model holds, there is not enough signal | 3 |

**That split is the deliverable.** A fitting script returns 27 numbers. This
returns 17 numbers and 10 documented reasons — and it separates the 7 cases
where a *better model* is needed from the 3 where *better data* is needed. Those
call for opposite actions by the experimentalist, and no misfit number
distinguishes them.

### Two verdicts worth reading side by side

`VERDICT/examples/example-zno-200c5-dark.md` — **permitted**. Misfit 6.6%, noise
4.2%, arc closed. Independent corroboration: the fit's R_s + R_gb = 7.320 MΩ
against a *directly measured* R_dc of 7.394 MΩ — 1.0% agreement on a quantity
the fit does not target.

`VERDICT/examples/example-zno-250c5-dark.md` — **refused, imprecise**. The arc
never closes, misfit 20.5%, and |Z| reaches 141 MΩ — far outside the trusted
range, drawing 0.14 nA. The residual is *random*, so the single-arc model is not
contradicted; there simply is not enough signal. That distinction is the
actionable part: no reanalysis and no better model fixes it. Raising the
excitation to 200 mV would.

### One finding, and one retraction

`FINDING/examples/example-effective-capacitance.md` — **supported**. Effective
capacitance in tens of pF across both sample sets, so the response is geometric
bulk capacitance, not grain boundaries (which would give nF–µF, three orders
away). Rests only on permitted verdicts; reproduces across independently grown
coupons.

`FINDING/examples/example-activation-energy.md` — **retracted**. An activation
energy of 251 meV had been fitted at R² = 0.949 across the deposition-temperature
axis. The line goes through the points; the arithmetic is fine. But that axis is
SYNTHESIS — three different films — so a rate law across it has units of energy
and no referent. Sample geometry, which was never divided out, accounts for more
than half of what remains.

**No goodness-of-fit statistic detects this.** Only the DATASET's axis
declaration does, which is why that field is required and gated.

---

## Why the refusals are the product

The kit exists because a table with a number in every row is indistinguishable
from a table of nonsense until something says which rows may be used. Here,
10 of 27 rows may not — and each carries the reason, the threshold that decided
it, and the ground-truth calibration that licensed the threshold.

Every threshold in those verdicts resolves to a CALIBRATION artifact, and
`graph_gate.py` G2 fails if one does not. Three of those calibrations exist
because the constant they license was found to be **wrong** — each had been
scored on a quantity insensitive to the damage it caused. See
`CALIBRATION/examples/example-weight-floor.md` for the clearest case.

---

## Reproduce it

```bash
tests/run_end_to_end.sh
```

Runs the emit step into a scratch directory, gates the result, verifies the
quoted numbers against provenance, and asserts the permitted/refused split.
Requires Python 3.9+ and numpy; `cfs` is optional and exercised if present.
