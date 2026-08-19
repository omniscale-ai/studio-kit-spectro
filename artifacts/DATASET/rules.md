# DATASET — Generation & Validation Rules

1. **Every condition axis is declared MEASUREMENT or SYNTHESIS.** A synthesis
   axis varies the sample; a measurement axis varies the measurement of one
   sample. Fitting a rate law across a synthesis axis produces a number with
   the right units and no meaning. Enforced by `graph_gate.py` G5.
2. **The trusted instrument range is stated, not assumed.** Give the signal
   level at both extremes of the sweep. Where signal approaches the noise
   floor, the data there is not noisy data — it is not data.
3. **Geometry is per sample, or declared missing.** If samples differ in the
   geometry that converts measurement to material property, that geometry
   varies with whatever axis it correlates with, and any trend along that axis
   is confounded until it is divided out.
4. **Instrument metadata is checked, not copied.** Sentinel values from
   disconnected sensors (implausible temperatures, zeroed channels) must be
   identified here rather than propagated into analysis as fact.
5. **Format traps are recorded.** Decimal commas, unusual encodings and
   silently-truncating parsers belong here; the next person will hit them too.
