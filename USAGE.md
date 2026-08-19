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
| point a VERDICT's Evidence at a calibration that does not exist | G2 | unresolved threshold licence |

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
    --map verdict=usability reasons=why
```

Then gate:

```bash
python3 scripts/graph_gate.py artifacts
```

If your verdicts cite calibrations you have not written yet, G2 will say so —
which is the point. Write them with `workflows/calibrate-threshold.md`.

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

The kit is not impedance-specific. To adapt it:

- **DATASET** — replace the impedance-flavoured trusted-range discussion with
  your instrument's. The requirement is that a range exists and is stated.
- **VERDICT** — the five criteria (identifiability, misfit, residual structure,
  noise, instrument range) are general to model fitting. Edit
  `artifacts/VERDICT/rules.md` if your domain needs a sixth; `graph_gate.py`
  reads its list from `REQUIRED_EVIDENCE`.
- **CALIBRATION** — unchanged. "Score on the quantity you care about, report
  both error rates, score the rule you deploy" is domain-independent.
- **FINDING** — the confound table's rows (geometry, axis kind, instrument
  range, selection) are a starting set; add your domain's.
