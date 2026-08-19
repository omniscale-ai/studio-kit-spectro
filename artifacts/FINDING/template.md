---
status: {proposed | supported | retracted}
date: {YYYY-MM-DD}
---

# {Finding title}

**ID**: `cpt-{system}-finding-{slug}`

## Claim

{The physical claim, stated so that it could be wrong. Include the quantity,
its value, and the population it is claimed over.}

## Supporting Verdicts

{Every VERDICT this rests on: `cpt-{system}-verdict-{slug}`.

A claim resting on refused verdicts is not supported by this data, whatever it
looks like on a plot.}

## Confounds Considered

| confound | could it produce this pattern? | excluded how |
|---|---|---|
| sample geometry | | |
| synthesis vs measurement axis | | |
| instrument range | | |
| selection (which measurements survived) | | |

{At minimum: does any quantity that varies with the claimed axis also vary for
a reason unrelated to the claim? If a geometric or instrumental factor moves
with the axis, its size must be compared against the claimed effect before the
effect is claimed at all.}

## Reproduction

{Does the claim hold in an independent sample set?

Give the within-group scatter against the between-group effect. An effect
smaller than its own replication scatter is not an effect — and a trend that
reverses sign between two sets grown and measured the same way is not a
property of the material.}
