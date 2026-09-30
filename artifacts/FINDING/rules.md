# FINDING — Generation & Validation Rules

1. **Findings rest on permitting verdicts.** `status: supported` requires that
   the verdicts it cites permit the parameters it uses. Enforced by
   `graph_gate.py` G4.
2. **Confounds are enumerated, not waved at.** Geometry, axis kind, instrument
   range and selection each get a row. "Unlikely" is not an exclusion.
3. **A rate law needs a MEASUREMENT axis.** Fitting one across a SYNTHESIS axis
   yields a number with the right units and no physical meaning, because each
   point is a different sample.
4. **Compare the effect to its replication scatter.** Within-group spread
   larger than the between-group trend means the trend is not resolved by this
   data, whatever the fit quality of the trend line.
5. **A sign reversal across sample sets retracts the finding**, it does not
   average with it.
6. **Supporting Verdicts lists only what the claim rests on.** A refused
   verdict mentioned there is read as support and fails G4 — which is correct.
   Where an exclusion needs discussing, it belongs in the selection row of
   Confounds Considered, since excluding measurements *is* a selection effect.
7. **Retraction is a first-class status.** A retracted finding keeps its
   artifact, with the reason. Deleting it loses the reason someone will
   otherwise rediscover.
8. **No supported claim on borrowed thresholds.** If any supporting verdict
   was judged against a CALIBRATION marked `basis: inherited`, the finding
   stays `proposed` until the threshold is re-scored on this system. Enforced
   by G4. A first look at new data on another system's thresholds is fine;
   a publication on them is the number nobody can defend.
