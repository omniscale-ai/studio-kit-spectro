# Constructor Studio Spectro Kit

A [Constructor Studio](https://github.com/constructorfabric/studio) kit for
**fitting models to measured spectra and knowing which fitted numbers you are
allowed to use.**

Fitting a curve is cheap. Deciding whether the resulting parameter means
anything is the entire problem, and it is where analyses quietly go wrong:

```
fit a curve (seconds)   ≪   establish that the parameter is determined,
                            unbiased, inside the instrument's range, and
                            not an artefact of the axis you plotted it against
```

So this kit makes **verdicts and their evidence first-class artifacts**. A
parameter leaves the pipeline with the reasons it may be believed attached, or
it does not leave.

## Artifact pipeline

```
DATASET ──▶ ARTEFACT-SCAN ──▶ FIT ──▶ VERDICT ──▶ FINDING
                                       ▲
                         CALIBRATION ──┘

ANALYSIS-PLAN gates all of it
```

- **DATASET** — instrument, trusted range, sample geometry, and every condition
  axis declared **MEASUREMENT** or **SYNTHESIS**.
- **ARTEFACT-SCAN** — what in the data cannot be trusted, detected across the
  series rather than per measurement. Script-generated.
- **FIT** — one model, one measurement: the equation, the weighting, the
  effective sample size, the parameters. Script-generated.
- **VERDICT** — may this parameter be used? Five criteria, each with its
  measured value, its threshold, and the calibration licensing that threshold.
  Script-generated, never hand-edited.
- **CALIBRATION** — the ground-truth evidence licensing one threshold or
  constant. Must name **the quantity it was scored on** and report **both**
  error rates.
- **FINDING** — a physical claim, with its confounds sized and its reproduction
  checked. `retracted` is a first-class status.

## The three rules that carry the kit

**1. No parameter without a verdict.** A number that leaves without one is a
number nobody can defend six months later.

**2. No threshold without a calibration that names its scored quantity.** A
constant tuned on quantity A while relied upon for quantity B is defensible on
its own terms and wrong in use. This is the commonest silent failure in a
fitting pipeline, and it is invisible to every goodness-of-fit statistic.

**3. Biased and imprecise are different verdicts.** Noisy data means widen the
uncertainty. A wrong model means no uncertainty covers the answer. Merging them
into "bad fit" throws away the only information that tells the experimentalist
what to do next.

## Gates (three layers)

1. `constraints.toml` — structure and traceability via `cfs validate`: required
   sections, ID grammar `cpt-{system}-{dataset|scan|fit|verdict|calib|finding|aplan}-{slug}`.
2. `scripts/` — computational gates. `emit_artifacts.py` *generates* FIT and
   VERDICT records from a pipeline's result table; `graph_gate.py` enforces
   seven cross-artifact rules that static validation cannot express.
3. `workflows/` — agent routes with hard rules (a parameter may never be
   reported without its verdict; a rate law may never be fitted across a
   synthesis axis).

Each `graph_gate.py` check exists because a real analysis failed that way. The
script's docstring names the failure next to the gate.

## Start here

**[`examples/end-to-end/`](examples/end-to-end/README.md)** — a complete run on
real data: what goes in, what happens, what comes out. 27 spectra in, 17 usable
numbers and 10 documented refusals out. `tests/run_end_to_end.sh` executes it
and asserts that outcome.

## Worked example: ZnO thin films by direct-write ALD

Two impedance datasets, 54 spectra, shipped in `artifacts/*/examples/`. Read in
this order:

```
DATASET/examples/example-zno-cseries.md        # geometry varies 3.96x with the axis
ARTEFACT-SCAN/examples/example-zno-750pass.md  # 50 Hz mains; notch beats truncate, scored
FIT/examples/example-zno-200c5-dark.md         # a well-determined arc
VERDICT/examples/example-zno-200c5-dark.md     # permitted, with independent corroboration
VERDICT/examples/example-zno-250c5-dark.md     # refused as imprecise — an instrument limit
CALIBRATION/examples/example-weight-floor.md   # a constant scored on the wrong quantity
FINDING/examples/example-activation-energy.md  # RETRACTED, and why
```

The retracted finding is the one to read first. An activation energy of
251 meV was fitted at R² = 0.949 across an axis that turned out to be the ALD
*deposition* temperature — three different films, all measured at one bench
temperature. The line went through the points. No fit statistic detects that,
which is why axis kind is a required, gated field in DATASET.

## Install

```bash
# from a checkout
cfs kit install --path . --install-mode copy

# once published
cfs kit install <org>/studio-kit-spectro
```

`--install-mode register` keeps a local kit in place instead of copying it —
valid only for paths inside the project root.

## Standalone

Everything here runs without Studio — Python 3.9+, **standard library only**:

```bash
python3 scripts/graph_gate.py artifacts     # 7 cross-artifact gates
python3 scripts/check_claims.py             # example numbers vs their provenance
```

See [USAGE.md](USAGE.md).

## Scope

Deliberately general: any spectroscopy where a model is fitted to measured data
and parameters are reported. The ZnO impedance case is the worked example, not
the boundary.

The CALIBRATION and VERDICT layers are domain-neutral by construction — "score
on the quantity you care about", "report both error rates" and "biased is not
imprecise" have nothing to do with impedance. DATASET and ARTEFACT-SCAN still
carry impedance-flavoured language in places, and adapting them to another
technique is the obvious next test of how general the shape really is; see
[USAGE.md](USAGE.md#5-adapting-to-your-domain).

## License

Apache 2.0.
