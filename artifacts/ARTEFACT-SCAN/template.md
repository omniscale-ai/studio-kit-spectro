---
status: {draft | complete}
date: {YYYY-MM-DD}
---

# {Artefact scan of <dataset>}

**ID**: `cpt-{system}-scan-{slug}`

## Dataset

{Reference: `cpt-{system}-dataset-{slug}`, and how many measurements scanned.}

## Contaminations

| where | detected how | measurements affected | evidence |
|---|---|---|---|
| {band/point} | {test} | {n of N} | {what makes it impossible, not merely odd} |

{For each: state the evidence that the points are WRONG rather than extreme.
A contaminated point that still looks physically plausible is the dangerous
case — it passes every per-point test while being badly wrong, and only shows
up across the series.}

## Working Window

{The retained range, and the rejection STRATEGY with its evidence:

- **notch** — remove the contaminated band, keep what lies beyond it
- **truncate** — cut the range at the contamination

Truncating also discards everything else in the removed range. Where the
discarded region carries information the analysis needs, say what is lost and
score the two strategies against a target neither is fitted to.}

## Attestation

{Script name, version/commit, exact invocation. Artefact scans are
script-generated: series-level detection is not something to do by eye.}
