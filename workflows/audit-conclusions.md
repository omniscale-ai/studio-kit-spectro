---
description: Invoke before publishing or acting on a physical claim drawn from fitted parameters — e.g. "we found an activation energy", "write up the conclusion", "does this trend hold". Tests the claim against what the data actually licenses.
---

# Workflow: audit-conclusions

## Inputs

- A proposed physical claim and the verdicts it rests on.

## Steps

1. **Check the axis kind first.** Look up every axis the claim spans in its
   DATASET. Is each MEASUREMENT or SYNTHESIS?

   A rate law, activation energy, or any response function requires a
   MEASUREMENT axis. Fitted across a SYNTHESIS axis it compares different
   samples, and returns a number with the right units and no referent. **No
   goodness-of-fit statistic detects this** — the line will go through the
   points with an excellent R², which is why this check is first and manual.

2. **Check the supporting verdicts permit the parameters used.** A claim resting
   on refused verdicts is not supported by this data, whatever the plot shows.
   Check both ends of any fitted trend: trends are anchored by their extremes,
   and extremes are where data is worst.

3. **Enumerate confounds and size them.** Geometry, axis kind, instrument range,
   selection. For each, ask not "is it plausible" but "how large is it compared
   with the claimed effect". A geometric factor spanning 4× against a 9× trend
   is not a footnote.

4. **Compare the effect with its own replication scatter.** Within-group spread
   larger than the between-group trend means the trend is not resolved. Report
   both numbers together, always.

5. **Check reproduction in an independent set.** Same sign? A trend that
   reverses between two sets grown and measured the same way is not a property
   of the material.

6. **Record the FINDING** with `status: supported`, `proposed` or `retracted`.

7. **Gate.** `python3 {scripts}/graph_gate.py <artifacts-root>` must PASS.

## Hard rules

- NEVER fit a rate law across a SYNTHESIS axis.
- NEVER report a material property without dividing out per-sample geometry, or
  stating that geometry was not recorded and the property is therefore
  unreportable.
- A retracted finding keeps its artifact and its reason. Deleting it loses the
  reason, and someone will rediscover the claim.
- Report within-group scatter alongside every between-group effect.
- If the claim survives all of this, say what would falsify it.
