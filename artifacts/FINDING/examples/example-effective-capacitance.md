---
status: supported
date: 2026-08-19
---

# The measured capacitance is geometric, not interfacial


<!-- toc -->

- [Claim](#claim)
- [Claimed Axis](#claimed-axis)
- [Supporting Verdicts](#supporting-verdicts)
- [Confounds Considered](#confounds-considered)
- [Reproduction](#reproduction)

<!-- /toc -->

**ID**: `cpt-zno-finding-effective-capacitance`
## Claim

The effective capacitance of these ZnO films,
C = (R^(1−α)·Q)^(1/α), is of order **tens of picofarads** — over dark spectra
whose verdicts permit the parameter, 31–98 pF in the 750-pass set and 24–68 pF
in the C-series (3.7–131 pF across all permitted spectra including illuminated
ones). Values in this range correspond to the
geometric (bulk) capacitance of the film, not to grain boundaries or electrode
processes, which would give nanofarads to microfarads.

The claim is about magnitude and its interpretation, not about any trend.

## Claimed Axis

`none` — this is a statement about the magnitude of a quantity over a
population, not a trend along a condition axis. Nothing is fitted against
deposition temperature, print speed or illumination; the claim would stand if
the grid had been a single coupon measured many times. That is also why it
survives while the activation-energy finding does not: it never crosses an axis
at all.

## Supporting Verdicts

Rests only on fits whose R_gb, Q and α are permitted, including
`cpt-zno-verdict-750pass-200c5-dark`. 17 permitted verdicts in the 750-pass set
and 7 in the C-series; the ranges quoted above are computed over those alone.

Coupons whose parameters are refused are excluded rather than included with a
caveat — see the selection row under Confounds Considered for what that
exclusion could and could not hide.

## Confounds Considered

| confound | could it produce this pattern? | excluded how |
|---|---|---|
| sample geometry | Only weakly. | The claim is an order-of-magnitude statement spanning a factor ~3 within the dark subsets, while the geometric factor spans 3.96× — so geometry could shift values within the range but cannot move tens of pF to the nF–µF that an interfacial interpretation requires. The three-order-of-magnitude gap is what carries the claim. |
| synthesis vs measurement axis | Not applicable. | No trend along any axis is claimed; the claim is about the magnitude observed in every permitted measurement. |
| instrument range | Yes, for refused coupons. | Excluded by construction: coupons outside the trusted range are not counted. |
| selection | Partially. | Permitted coupons are the better-behaved ones, so *which* films are represented is biased. The capacitance scale is not: the refused coupons — e.g. `cpt-zno-verdict-cseries-250c5-dark` — carry nominal values in the same tens of pF, so including them would not move the order of magnitude the claim rests on. |
| definitional artefact | Yes, worth stating. | C = (R^(1−α)Q)^(1/α) is algebraically identical to τ/R given τ = (R·Q)^(1/α). Reporting both is one quantity, not a cross-check, and this claim rests on one number. |

## Reproduction

**Reproduces across both sample sets.** 750-pass 31–98 pF, C-series 24–68 pF —
overlapping ranges from independently grown coupons measured three weeks apart.
An independent prior analysis of the 750-pass set reported 35–78 pF by a
different route, consistent with the values here.

This is the one physical conclusion in this project that survives the checks in
`cpt-zno-finding-activation-energy`: it does not depend on the axis kind,
it is not moved by the geometric confound at the order of magnitude that
matters, and it does not reverse between sets.
