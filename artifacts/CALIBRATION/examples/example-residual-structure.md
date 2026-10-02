---
status: complete
date: 2026-08-19
scope: zno
basis: scored
---

# Calibration — systematic-residual rule (noisy data vs wrong model)


<!-- toc -->

- [Question](#question)
- [Scored Quantity](#scored-quantity)
- [Ground Truth](#ground-truth)
- [Result](#result)
- [Error Rates](#error-rates)
- [Attestation](#attestation)

<!-- /toc -->

**ID**: `cpt-zno-calib-residual-structure`
## Question

The rule that decides whether a poor fit means **noisy data** (parameter
imprecise) or a **wrong model** (parameter biased). Used by
`eis_suite.verdict.residual_structure` and by `usability`, which attaches
"single arc is the wrong model" to a verdict.

The distinction matters because the two demand opposite responses: noise means
widen the uncertainty, wrong model means no uncertainty covers the answer.

## Scored Quantity

**Scored on the true generating model** — whether the rule fires on spectra
that genuinely are a single depressed arc versus spectra that are not.

**Not scored on**: fit quality. A rule that fires whenever a fit is poor
measures fit quality, not model error, and would be useless for the decision it
exists to make.

## Ground Truth

The `bench_synth.py` grid, partitioned by true model: 89 true single CPE arcs;
9 Cole–Cole distributions (a log-normal spread of RC elements, not representable
by one CPE arc); 9 two-arc cases at 1.5 decades; 9 at 0.7 decades.

Statistic: Wald–Wolfowitz runs test on sign(|Z| − |Z_fit|) over arc-bearing
points, ordered by frequency.

## Result

| rule | false positive (true single arc) | detection (non-single truths) |
|---|---|---|
| runs test alone | **35%** | 44–89% |
| **runs test AND misfit > 10% (deployed)** | **6%** | 37% (78% for two arcs 1.5 decades apart) |

Only the conjunction is deployed, and only the conjunction is reportable. On the
real data 13 of 54 spectra meet it.

**The runs test alone is not usable as a claim.** It detects *any* systematic
departure once precision is sufficient — including the small compromise a
weighted least-squares fit always leaves. On true single arcs it fires 81% of
the time at 0.5% noise, 38% at 2%, and 4% at 5%: its power *falls* as noise
rises.

That also corrects a plausible-sounding rule of thumb: "low noise with a poor
fit means the model is wrong" is **false in general** — at low noise the test
fires on correct models too. What makes the deployed rule safe is the misfit
gate, not the low noise.

## Error Rates

Detection 37% (78% on well-separated two-arc cases); **false positive 6%** on
89 spectra known to be single arcs. Both measured on the deployed conjunction,
not on the component statistic — whose false-positive rate is 35%, nearly six
times worse.

## Attestation

`exp_resid_validation.py`, eis_suite @ 2026-08-19 on impedance 1.7.1+eis.1
(fork of ECSHackWeek/impedance.py @ 6a269c4), deterministic seeds from
`bench_synth.build_cases()`.
