---
status: complete
date: 2026-08-19
---

# Calibration — which misfit statistic separates good fits from bad


<!-- toc -->

- [Question](#question)
- [Scored Quantity](#scored-quantity)
- [Ground Truth](#ground-truth)
- [Result](#result)
- [Error Rates](#error-rates)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-calib-misfit-metric`
## Question

The definition of `misfit` used by every VERDICT's misfit criterion, and its
0.15 threshold in `eis_suite.verdict.usability`.

## Scored Quantity

**Scored on separating fits judged good from fits judged bad by eye**, on real
spectra, before the statistic was chosen.

**Not scored on**: agreement with any single fitted parameter. The failure this
statistic must catch is a curve drawn through empty space, which every
parameter-based score is blind to by construction — the parameters of such a
fit are internally consistent, they are just not about the data.

## Ground Truth

Twelve real spectra from both ZnO sets, split into six clearly good and six
clearly bad by inspection of the Nyquist plots, *then* scored. Judgement was
recorded before computing the candidates.

## Result

| statistic | good (max) | bad (min) | separates? |
|---|---|---|---|
| median(\|d\|) / p90(\|Z\|) — scale-normalised | 3.8% | 2.0% | **no, overlaps** |
| median(\|d\|/\|Z\|) — per-point relative | 26.1% | 32.9% | yes, narrowly |
| **median over arc-bearing points (\|Z\| > 10% of scale)** | **9.9%** | **24.8%** | **yes, 2.5× margin** |

The scale-normalised form was in use and is the reason 250 °C scatter clouds —
with no arc in them at all — scored 0.6–6.8% and were graded trustworthy. The
many high-frequency points sit at |Z| ~ 10⁻³ of the arc, so their absolute
distance is negligible whatever they do, and they dominate the median.

The obvious fix fails the other way: per-point relative error is dominated by
those same points for the mirror-image reason (the model predicts R_s there
while the data is scatter), scoring visibly excellent fits at 26%.

Threshold 0.15 sits in the gap; the choice is insensitive between 0.10 and 0.20.

## Error Rates

On the held-out synthetic benchmark with the chosen statistic and threshold:
spectra called trustworthy recover R_dc to median 2.7% / p90 8.9%; rejected
spectra have median error 12–14%; **9 of 9** deliberately truncated arcs are
correctly refused (the previous statistic caught 8 of 9).

**False positive**: 5 of 89 true single arcs (6%) are refused on the conjunction
that includes this statistic — see `cpt-zno-calib-residual-structure`.

## Attestation

`eis_suite.fit.misfit` (definition), `bench_synth.py` (rates),
eis_suite @ 2026-08-19.
