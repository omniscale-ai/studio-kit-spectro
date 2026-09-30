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
- **VERDICT** — may this parameter be used? Five criteria every model fit
  has, plus whatever the ANALYSIS-PLAN declares for this system — each with
  its measured value, its threshold, and the calibration licensing that
  threshold. Script-generated, never hand-edited.
- **CALIBRATION** — the ground-truth evidence licensing one threshold or
  constant. Must name **the quantity it was scored on**, report **both**
  error rates, and declare **which system it is valid for** — a threshold
  borrowed from another system is recorded as `inherited`, licenses
  provisional verdicts, and licenses no supported finding.
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
   ten cross-artifact rules that static validation cannot express.
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

## The kit does not ship a fitter

It is not missing one. The chain starts at a **result table**: one row per
measurement, from whatever pipeline produced the fits. `--map` exists so that
pipeline can be anyone's. Producing the table is the analyst's work; this kit's
job begins at the point where a number wants to be believed.

Two consequences worth stating, because a first-time user reliably hits both.
Bringing your own fitter means **its thresholds are yours to calibrate** —
`workflows/calibrate-threshold.md`, scored on the quantity you actually rely on,
with both error rates. And the calibrations shipped in `artifacts/*/examples/`
are **evidence about ZnO impedance at one scale**; copying their numbers onto a
different instrument or material is the precise failure the kit exists to stop.
They are worked examples of the form, not defaults — and since 2026-09-30 the
gate enforces this: a CALIBRATION carries a `scope:`, a VERDICT may not cite
one scoped to another system (G3), and a threshold you borrow anyway must be
written down as `basis: inherited`, which licenses provisional verdicts and no
`supported` finding (G4). The second field test did exactly this borrowing,
correctly and in prose; the gate could not see it.

## Nothing about the model is the kit's

The kit was built on single-arc impedance spectra, and its first version
carried that in places it should not have: the emitter's default parameter
list was one circuit's, its identifiability row said "arc closed", and the
verdict's required criteria were a fixed five with no way to add the one a
both-ways sweep needs. Pointing it at a second technique (XRD) and a second
impedance programme (MIS capacitors, kΩ scale, swept both ways) found each of
these. They are now **declarations, not defaults**:

| what varies between systems | where it is declared | what gates it |
|---|---|---|
| the parameters a fit yields | `emit_artifacts.py --params` (required) | — |
| the identifiability test — a property of the *model* ("arc apex inside the window"; "peak and both half-maxima inside the scan") | `--identifiability-test`, printed in every VERDICT | G1 |
| what the misfit statistic measures | `--misfit-label` | — |
| criteria beyond the universal five | ANALYSIS-PLAN → `Verdict Criteria` | G1 requires each in every permitting VERDICT of the system |
| which system a threshold is evidence about | CALIBRATION → `scope:`, `basis:` | G3 (scope), G4 (no supported claim on inherited) |
| how the independent variable was traversed, once or both ways | DATASET → `Acquisition Order` | G10 |

`tests/test_domain.py` exercises every row on a synthetic system the kit was
not written for.

## Tests

```bash
tests/run_all.sh
```

Three layers, in increasing order of what they can catch:

| suite | what it catches |
|---|---|
| `run_end_to_end.sh` | the chain stopped working — replays a real dataset, asserts 17 permitted / 10 refused, split 7 biased and 3 imprecise |
| `test_routing.py` | a verdict meaning different things to the emitter and to the gate; generated artifacts missing the `<!-- toc -->` block `cfs validate` requires; an extra Evidence criterion citing a calibration that does not exist |
| `test_noise.py` | the routing itself: noisy → *imprecise*, mis-modelled → *biased*, unidentifiable → refused even when the fit is excellent |
| `test_completeness.py` | a second emit from one DATASET erasing the first from the ledger G8 reads |
| `test_axis_kind.py` | a `supported` claim fitted along an axis the DATASET declares SYNTHESIS |
| `test_domain.py` | the kit on a system it was not written for: a plan-declared criterion is required (G1); a calibration from another system is refused (G3); a borrowed one licenses verdicts but no supported finding (G4); a DATASET states its acquisition order (G10); the emitter assumes no model |

The last one needs synthetic data, and that is the point: the real dataset
carries no label saying which measurements are genuinely noisy and which are
genuinely mis-modelled, so it can show that the chain *runs* but never that it
*routes correctly*. `tests/synth.py` builds a whole system — its own DATASET,
ARTEFACT-SCAN, CALIBRATIONs and ANALYSIS-PLAN — with truth known by
construction, which also exercises the path a new user takes.

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
python3 scripts/graph_gate.py artifacts     # 10 cross-artifact gates
python3 scripts/check_claims.py             # example numbers vs their provenance
```

See [USAGE.md](USAGE.md).

## Scope

Deliberately general: any spectroscopy where a model is fitted to measured data
and parameters are reported. The ZnO impedance case is the worked example, not
the boundary.

The CALIBRATION and VERDICT layers are domain-neutral by construction — "score
on the quantity you care about", "report both error rates" and "biased is not
imprecise" have nothing to do with impedance. What a technique adds — its
model's identifiability test, its own verdict criteria, its acquisition
order — is declared per system rather than edited into the kit; see
[USAGE.md](USAGE.md#5-adapting-to-your-domain). The shipped examples are ZnO
impedance and are scoped to it.

## License

Apache 2.0.
