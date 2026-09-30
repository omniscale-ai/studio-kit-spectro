---
description: Invoke when the user asks to analyse a new spectrum dataset, or before any heavy analysis work — e.g. "analyse this EIS data", "what can we get out of these spectra", "start on the new dataset". Produces an approved ANALYSIS-PLAN, which gates every other workflow in this kit.
---

# Workflow: plan-analysis

## Inputs

- A dataset the user wants analysed, or a question they want answered.

## Steps

1. **Establish the question, and the quantity that answers it.** Not "analyse
   the spectra" — which number, and what would count as an answer. If no
   measured quantity answers the question, say so now: that is a finding, and
   it is cheaper delivered on day one than on day eight.

2. **Register the DATASET before anything else.** Fill
   `artifacts/DATASET/template.md`. Two sections decide whether later
   conclusions can exist at all, so do not defer them:
   - **Condition Axes** — every axis declared MEASUREMENT or SYNTHESIS. Ask the
     experimentalist directly; file names and folder structure do not say which,
     and guessing here has produced published errors.
   - **Instrument** — the range over which the instrument is trusted, with the
     signal level at both extremes. If nobody knows it, that is the first thing
     to measure.
   - **Acquisition Order** — which way the independent variable was
     traversed, once or both ways. Two programmes were once compared as if
     alike, one swept high→low and the other low→high→low, on films where the
     two directions disagree by 6%. If both ways: `direction` is a
     MEASUREMENT axis, and its disagreement is a verdict criterion (step 3b).

3. **Check the geometry.** If measurements will be converted to material
   properties, is per-sample geometry recorded? Does any geometric factor
   correlate with a condition axis? Note the size of the correlation now: if it
   is comparable to the effect the user hopes to find, tell them before the work
   starts, not after.

3b. **Declare what a verdict must answer for THIS system.** The five criteria
   every model fit has are the floor. Write anything this technique or this
   acquisition adds under the plan's Verdict Criteria — forward/reverse
   disagreement, an independent corroboration, a crystallinity floor — and G1
   will require it of every permitting VERDICT. Name the identifiability test
   for the model being fitted in the Decisions Log; it is the model's, not the
   kit's. Say which CALIBRATIONs exist for this system and which are to be
   borrowed (`basis: inherited`) for a first look and re-scored before any
   claim.

4. **Brainstorm scope, depth, interventions and budget with the user.** Present
   options with trade-offs and record them in the Decisions Log. Include the
   question "is refusing to report a number an acceptable deliverable?" — if the
   answer is no, this kit is the wrong tool.

5. **Get approval.** Fill Approval with a person and a date; set
   `status: approved`.

6. **Gate.** `python3 {scripts}/graph_gate.py <artifacts-root>` must PASS.

## Hard rules

- NEVER begin fitting before the DATASET's Condition Axes are declared. A trend
  fitted along an axis of unknown kind cannot be interpreted afterwards.
- NEVER assume an axis is a measurement axis because it has physical units.
  Temperature, pressure and voltage are all commonly synthesis parameters.
- If the user cannot say whether an axis is measurement or synthesis, stop and
  find out. This is a five-minute question that invalidates weeks of work.
