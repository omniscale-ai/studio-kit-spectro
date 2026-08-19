---
status: {draft | registered}
date: {YYYY-MM-DD}
---

# {Dataset name}

**ID**: `cpt-{system}-dataset-{slug}`

## Instrument

{Instrument and model. Excitation amplitude and bias. Swept range, points per
decade, file format and any parsing traps (encoding, decimal separator).

Then the part most datasets omit: THE RANGE OVER WHICH THE INSTRUMENT IS
TRUSTED. State the signal level at the extremes of the measured range. A range
you have not bounded is a range you have not checked, and the analysis will
faithfully fit whatever the instrument returned outside it.}

## Condition Axes

{One row per axis. Declare each MEASUREMENT or SYNTHESIS.}

| axis | values | kind | note |
|---|---|---|---|
| {e.g. bias} | {…} | MEASUREMENT | varies the measurement of one sample |
| {e.g. growth temperature} | {…} | SYNTHESIS | each value is a different sample |

{A trend fitted across a SYNTHESIS axis describes how making the sample
differently changed it. It is not a response of one sample to a variable, and
no rate law may be fitted to it.}

## Sample Geometry

{Per-sample geometry needed to turn measured quantities into material
properties, with the conversion written out. If it was not recorded, say so
explicitly and list which quantities are therefore unreportable — an omission
here silently becomes a confound later.}

## Provenance

{Files, acquisition dates and sessions, operator, instrument log quirks
(disconnected sensors reporting sentinel values, etc.).}
