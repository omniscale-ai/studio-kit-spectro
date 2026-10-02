# Using the Spectro Kit

No Constructor Studio installation is needed for the standalone workflow — just
`python3` (3.9+, stdlib only).

## 0. Get the kit

```bash
cd studio-kit-spectro
```

## 1. Tour the artifact chain (10 minutes, read-only)

One worked example runs end to end. Read in this order:

```
artifacts/DATASET/examples/example-zno-cseries.md         # what was measured, and on what
artifacts/ARTEFACT-SCAN/examples/example-zno-750pass.md   # what in it cannot be trusted
artifacts/FIT/examples/example-zno-200c5-dark.md          # one fit, with its weighting licensed
artifacts/VERDICT/examples/example-zno-200c5-dark.md      # may we use this number? yes, because…
artifacts/VERDICT/examples/example-zno-250c5-dark.md      # …and here, no, because…
artifacts/CALIBRATION/examples/example-weight-floor.md    # where a threshold came from
artifacts/FINDING/examples/example-activation-energy.md   # a retraction, with reasons
```

Every kind has `template.md` (structure), `rules.md` (hard rules) and
`checklist.md` (review questions) beside its examples.

**If you read only one file**, make it the retracted finding. It is a real
conclusion from a real report, fitted at R² = 0.949, that does not survive
contact with the axis it was plotted against.

## 2. Run the semantic gate

```bash
python3 scripts/graph_gate.py artifacts
```

Expected: `14 artifacts scanned` … `PASS`.

**Try breaking it.** Open `artifacts/CALIBRATION/examples/example-weight-floor.md`,
replace the Error Rates section with "The rule detects the problem reliably.",
and re-run:

```
[G3] Error Rates states no false-positive rate; detection alone is not a
     calibration, since a rule that fires on everything detects everything
FAIL — 1 violation(s)
```

Other things worth breaking, to see what the gates are for:

| edit | gate | what it says |
|---|---|---|
| set the retracted finding to `status: supported` | G4 | it rests on refusing verdicts |
| delete a row's `SYNTHESIS` marker in a DATASET | G5 | the axis kind is undeclared |
| remove the Attestation from a VERDICT | G7 | records of automated steps must name the script |
| delete one dataset's FIT and VERDICT files | G8 | the tree lacks artifacts `emitted.json` says were written |
| point a VERDICT's Evidence at a calibration that does not exist | G2 | unresolved threshold licence |
| mark a finding `supported` whose Claimed Axis is a SYNTHESIS row | G9 | every value of that axis is a different sample, so the trend is a synthesis contrast |
| omit a criterion from a permitting VERDICT's Evidence | G1 | a verdict must speak to all five, and to every one the plan declares |
| state a detection rate with no false-positive rate | G3 | a rule that fires on everything detects everything |
| mark an ANALYSIS-PLAN `approved` with an empty Approval | G6 | approval must name who and when |
| cite a CALIBRATION whose `scope:` is another system | G3 | a threshold is evidence about the data it was scored on |
| mark a finding `supported` on verdicts judged against a `basis: inherited` calibration | G4 | borrowed thresholds license verdicts, not claims |
| delete a DATASET's Acquisition Order | G10 | datasets swept in opposite directions are not comparable until this is stated |

## 3. Generate FIT and VERDICT artifacts from your own pipeline

`emit_artifacts.py` takes a CSV with one row per measurement. Column names are
supplied by `--map`, so it is not tied to any one analysis package.

```bash
python3 scripts/emit_artifacts.py results.csv \
    --system mysys \
    --dataset cpt-mysys-dataset-run1 \
    --scan    cpt-mysys-scan-run1 \
    --out artifacts \
    --model 'Z(w) = R_s + 1/(1/R_p + Q (jw)^alpha)' \
    --weighting 'sigma_i = sqrt((0.02|Z_i|)^2 + (0.002 p90|Z|)^2)' \
    --weighting-calib cpt-mysys-calib-weighting \
    --misfit-calib    cpt-mysys-calib-misfit \
    --residual-calib  cpt-mysys-calib-residual \
    --attest 'mypipeline v1.2, python run.py run1' \
    --params R_s,R_p,Q,alpha \
    --identifiability-test 'arc apex inside the window' \
    --misfit-label 'median relative deviation over the arc' \
    --map verdict=usability reasons=why identifiable=apex_in_window
```

`--params` and `--identifiability-test` are the two places a model enters the
record, and both are yours: the kit ships no parameter list and no test.


**Per-criterion calibrations.** By default the identifiability and
instrument-range rows cite `--misfit-calib` and `--weighting-calib`. If a
different calibration licensed them — a window study, say — name it, or the
Evidence table cites a real artifact that never scored that criterion and G2
passes because the id resolves:

```bash
    --identifiability-calib cpt-mysys-calib-window \
    --range-calib           cpt-mysys-calib-window \
    --noise-calib           cpt-mysys-calib-noise \
    --resid-rule 'amplitude > 0.003 AND |z| > 3'
```

`--resid-rule` matters when the deployed rule is not of the form the default
phrasing assumes (`systematic and misfit > X`). **The rule that is calibrated
must be the rule that is printed** — a conjunction has error rates its
components do not.

`emit_artifacts.py` refuses to overwrite: if two measurements slugify to the
same artifact id — which happens when labels are conditions rather than sample
ids, and two datasets share a grid — it exits 2 rather than silently replacing
the first dataset's records. Give the labels a per-dataset prefix, or emit each
dataset under its own `--out`. It also writes `emitted.json`, a ledger of what
it produced; gate G8 checks the tree against it.

Then gate:

```bash
python3 scripts/graph_gate.py artifacts
```

If your verdicts cite calibrations you have not written yet, G2 will say so —
which is the point. Write them with `workflows/calibrate-threshold.md`.

## 3b. Check the worked example against its provenance

```bash
python3 scripts/check_claims.py --verbose
```

Every number quoted in `artifacts/*/examples/` is read **out of the artifact**
and re-derived from the tables in `tests/provenance/`. The kit ships that data
rather than pointing at it, on its own principle: an artifact quoting a number
ships with the evidence for it.

This exists because the examples went stale once — tightening the verdict
criteria upstream silently invalidated numbers in a shipped artifact. Try it:
change `6.6%` to `9.9%` in the misfit row of
`artifacts/VERDICT/examples/example-zno-200c5-dark.md` and re-run.

A first version of this check compared numbers kept *in the script* against the
data, never reading the artifact — so it passed while the artifact said
something else. If you extend it, make sure your new claim actually fails when
you edit the artifact.

## 4. The workflows

With Studio installed these surface as `cf-*` skills. Standalone, they are
readable procedures:

| workflow | when |
|---|---|
| `plan-analysis` | before any heavy work; produces the ANALYSIS-PLAN that gates the rest |
| `analyse-spectra` | screen, fit, judge; emits FIT and VERDICT |
| `calibrate-threshold` | any time a constant needs justifying or changing |
| `audit-conclusions` | before publishing a physical claim |

`audit-conclusions` is the one that pays for itself. Its first step is checking
whether the axis your trend spans is a measurement axis or a synthesis axis, and
that single question has invalidated a published activation energy in this
kit's own worked example.

## 5. Adapting to your domain

The kit assumes a model is fitted to measured data and a parameter is wanted.
It assumes no model and no technique. Everything a technique adds is
**declared** — per run, per plan, per calibration — and gated; nothing is
edited into the scripts.

| what your system has | declare it | gate |
|---|---|---|
| its own fitted parameters | `emit_artifacts.py --params a,b,c` (required; there is no default list) | — |
| its own identifiability test — this belongs to the **model**: "arc apex inside the window" for a single arc, "peak maximum and both half-maxima inside the scan" for a diffraction line | `--identifiability-test '…'`, printed verbatim in every VERDICT; the column it reads is `--map identifiable=<col>` (`arc_closed` still read for old tables) | G1 |
| its own misfit statistic | `--misfit-label '…'` | — |
| criteria beyond the universal five | the ANALYSIS-PLAN's `## Verdict Criteria` table, one per row; emit the row with `--extra-criterion 'LABEL\|VALUE\|THRESHOLD\|CALIB-ID'` | G1 requires each row in every permitting VERDICT of the system; G2 requires its calibration to resolve |
| thresholds scored on THIS data | a CALIBRATION with `scope: <system>` and `basis: scored` | G3: a VERDICT may not cite a calibration scoped elsewhere |
| thresholds borrowed for a first look | a CALIBRATION in your system with `basis: inherited` and `inherited_from: <source id>` | G3 requires the source; G4 refuses a `supported` FINDING resting on it |
| an acquisition order — which way, once or both ways | DATASET `## Acquisition Order`; if both ways, `direction` is a MEASUREMENT axis and one FIT per direction | G10 |

A worked case, from the second field test. MIS capacitors swept
100 Hz → 5 MHz → 100 Hz, judged on thresholds scored on ZnO spectra swept the
other way at a thousand times the impedance:

```bash
# the plan declares what this system's verdicts must answer
## Verdict Criteria
| criterion | why |
|---|---|
| direction hysteresis | swept both ways; the branches must agree before either is a measurement |

# the borrowed thresholds are written down as borrowed
---
scope: ulk
basis: inherited
inherited_from: cpt-zno-calib-misfit-metric
---
… scored on MΩ-scale ZnO spectra; not re-scored at kΩ scale …

# the emit declares the model's test and the extra criterion
python3 scripts/emit_artifacts.py results.csv --system ulk … \
    --params R_s,R_p,Q,alpha \
    --identifiability-test 'single-arc model: arc apex inside the window' \
    --extra-criterion 'direction hysteresis|hyst_med|< 5%|cpt-ulk-calib-hysteresis'
```

The tree then passes with 141 provisional verdicts and **cannot** carry a
`supported` finding until the three calibrations are re-scored at ULK scale —
which is the correct state for that data, and the state the first version of
this kit could not express.

The five criteria themselves (identifiability, misfit, residual structure,
noise, instrument range) are not adjustable downward. They are properties of
fitting a model to data, not of any technique; a system that believes it does
not need one of them should write the row and say why the threshold is trivial.
