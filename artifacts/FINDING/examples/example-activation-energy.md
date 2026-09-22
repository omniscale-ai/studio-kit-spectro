---
status: retracted
date: 2026-08-19
---

# Retracted — "conduction activation energy 251 meV in ZnO"


<!-- toc -->

- [Claim](#claim)
- [Supporting Verdicts](#supporting-verdicts)
- [Confounds Considered](#confounds-considered)
- [Reproduction](#reproduction)

<!-- /toc -->

**ID**: `cpt-zno-finding-activation-energy`
## Claim

*As originally stated:* fitting R(T) = R₀·exp(Eₐ/kT) to the dark-spectrum
resistances across the 150 / 200 / 250 °C labels gives Eₐ = 251 meV
(R² = 0.949), a value characteristic of shallow donor or defect levels in ZnO.

**This claim is retracted.** It is not an activation energy. Three independent
reasons follow, each sufficient on its own.

## Claimed Axis

`deposition temperature` in `cpt-zno-dataset-cseries`.

That axis is declared **SYNTHESIS**, and this is the whole reason the claim is
retracted: every value of it is a different film, all measured at one bench
temperature, so `R(T) = R₀·exp(Eₐ/kT)` fitted along it returns a number with
units of energy describing a synthesis trend. Had G9 existed when this was
written, `status: supported` would have been refused here rather than caught a
month later by reading the file headers.

## Supporting Verdicts

Originally rested on the dark-spectrum resistances of both sets, including:

- `cpt-zno-verdict-750pass-200c5-dark` — permitted
- `cpt-zno-verdict-cseries-250c5-dark` — **refused** (imprecise; impedance
  outside the trusted instrument range)

The 250 °C C-series group anchors one end of the fitted line, and its
parameters are refused. In the 750-pass set the low-temperature end is anchored
by the 150 °C group, whose DRT peaks track the window edge rather than staying
put — they are artefacts of an unclosed arc, so their τ and R are not physical
either.

Both ends of the line rest on parameters this pipeline does not permit.

## Confounds Considered

| confound | could it produce this pattern? | excluded how |
|---|---|---|
| **synthesis vs measurement axis** | **Yes — decisively.** | Not excluded. `cpt-zno-dataset-750pass` and `cpt-zno-dataset-cseries` both declare deposition temperature a SYNTHESIS axis: each label is a *different film*, and all were measured at one bench temperature in a single session with the temperature channel disconnected. A rate law across this axis compares three films, not one film at three temperatures. The Arrhenius form has no referent here. |
| **sample geometry** | **Yes, ~30% of the effect.** | Not excluded. C-series geometric factor L/(w·d) spans 3.96× across the same axis, against a 9.4× resistance trend. For the 750-pass set only thickness is recorded (2.25×); dividing it out moves the fitted pseudo-energy 268 → 115 meV — more than half the number. Electrode geometry was never divided out at all. |
| **instrument range** | Yes, at the high-resistance end. | Not excluded. The most resistive coupons exceed the 30 MΩ trusted ceiling; their resistances are unconstrained fit outputs. |
| **selection** | Yes. | Not excluded. Which spectra survived to enter the fit correlates with impedance, hence with the axis being fitted. |

## Reproduction

**It cannot be checked in the replicate set.** Same nominal condition grid, two
sample sets grown and measured the same way — counting only spectra whose
verdicts permit the parameter:

| set | 150 °C | 200 °C | 250 °C | pseudo-Eₐ |
|---|---|---|---|---|
| 750-pass, R_gb | 21.2 MΩ (n=1) | 9.9 (n=2) | 5.2 (n=2) | **+268 meV** |
| 750-pass, R_dc measured | 23.3 MΩ | 10.1 | 5.7 | **+269 meV** |
| 750-pass, thickness divided out | — | — | — | **+115 meV** |
| C-series, R_gb | 1.74 MΩ (n=1) | **none usable** | 57.7 (n=1) | not fittable |

The C-series has one usable dark spectrum at 150 °C, none at 200 °C and one at
250 °C, so it produces no estimate. **Non-reproduction here means untested, not
contradicted** — a weaker statement than the one made in an earlier version of
this artifact, which reported a C-series trend of −408 meV and described the
effect as reversing sign. That figure came from a script that silently
substituted *refused* spectra where no permitted one existed. Withdrawn.

Note that the 750-pass figure has converged on the number being questioned:
**268 meV against the reported 251 meV.** The disagreement was never about the
arithmetic. It is about what the x-axis is — and thickness alone accounts for
more than half of it (268 → 115 meV).

**Retained lesson.** Nothing about the fit was wrong: R² = 0.949 is real, and
the line goes through the points. What was wrong was the referent of the x-axis.
No goodness-of-fit statistic can detect that, which is why the DATASET
declaration of axis kind is a required, gated field.
