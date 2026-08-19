# ANALYSIS-PLAN — Generation & Validation Rules

1. **The plan gates the work.** Analysis workflows check for an approved plan
   before heavy or irreversible steps.
2. **Name the quantity that answers the question.** If none does, stop and say
   so; that is a more valuable output than a number that does not mean what the
   question asked.
3. **Changing a calibrated constant is ask-first.** Recalibrating because a
   result looks wrong is legitimate only when the recalibration is scored
   against ground truth and recorded as a new CALIBRATION.
4. **Approval is a person and a date.** Enforced by `graph_gate.py` G6.
