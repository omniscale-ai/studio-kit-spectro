# ARTEFACT-SCAN — Generation & Validation Rules

1. **Scan the series, not the measurement.** A contaminant at a fixed position
   in the independent variable looks like an outlier in one measurement and is
   unmistakable across twenty. Per-measurement outlier rejection will miss it
   and will instead remove real structure.
2. **Physical-impossibility tests come first, plausibility second.** Points
   violating a sign or passivity constraint are certainly wrong. But the
   contaminants that cost the most are those that remain plausible per-point —
   these need the series view.
3. **Detection is data-driven.** Do not hard-code the contaminated band. Derive
   it and report what was derived; a hard-coded band is silently wrong on the
   next instrument.
4. **Notch versus truncate is a scored decision, not a habit.** Score both
   against a quantity neither is fitted to and record the result in Working
   Window.
5. **Nothing is dropped silently.** Every removed point is counted and
   attributed to a named cause in Contaminations.
6. **Script-generated.** Enforced by `graph_gate.py` G7.
