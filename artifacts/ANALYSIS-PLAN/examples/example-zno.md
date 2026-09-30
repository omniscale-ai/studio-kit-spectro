---
status: approved
date: 2026-08-19
---

# Analysis plan — ZnO impedance, what is recoverable


<!-- toc -->

- [Question](#question)
- [Scope](#scope)
- [Allowed Interventions](#allowed-interventions)
- [Deliverables](#deliverables)
- [Decisions Log](#decisions-log)
- [Verdict Criteria](#verdict-criteria)
- [Approval](#approval)

<!-- /toc -->

**ID**: `cpt-zno-aplan-recoverable`
## Question

What material properties of these ZnO films can be established from the two
impedance datasets, and with what confidence?

The quantity that answers it is the low-frequency resistance R_dc (and R_gb from
the fitted arc where it is identifiable), plus the effective capacitance. Where
neither is determined, saying so is the deliverable.

## Scope

In scope: `cpt-zno-dataset-750pass`, `cpt-zno-dataset-cseries`.

Out of scope: the IV and dynamic-photocurrent measurements; the A and B
replicate sets (no EIS acquired); any claim requiring temperature-resolved
measurement, since neither dataset contains a measurement-temperature axis.

## Allowed Interventions

- Screening artefact-contaminated points, with every removal counted and caused
- Refusing to report parameters, including refusing a whole condition group
- Retracting a previously published finding, with its artifact retained
- Re-running calibrations against synthetic ground truth

Ask-first: changing any calibrated constant; adding a model with more free
parameters (a two-arc fit halves the misfit on several spectra, but arc counting
is not recoverable at this data quality, so fitting one would move the error
somewhere less visible); contacting the experimentalists.

## Deliverables

- One report covering methods, results and every spectrum
- CALIBRATION artifacts for every constant the pipeline relies on
- Explicit instrument recommendations where the limit is the measurement, not
  the analysis

## Decisions Log

| question | options and trade-offs | choice |
|---|---|---|
| mains removal | truncate the window (simple, loses the arc-closure evidence) vs notch the band (keeps 10–31 Hz, more code) | notch — scored 4.6% vs 16.9% against measured R_dc |
| KK validity | veto usability vs report as diagnostic | diagnostic; the veto rejected 41 accurate spectra and admitted inaccurate ones. Safe only because these samples were shown stationary |
| arc count | fit two arcs where χ² improves vs refuse to count | refuse — all three DRT arms fail on two-arc synthetics at this corruption level, so "one arc" is not evidence of one arc |
| what to do about high-resistance coupons | report with wide error bars vs refuse | refuse, and recommend 200 mV excitation — the limit is signal current, not analysis |

## Verdict Criteria

Nothing beyond the five. The identifiability test for this system's single-arc
model is *arc apex inside the window with −Z″ falling on the low-frequency
side*; it is a property of the model and is printed in every VERDICT, not
assumed. Independent R_dc corroboration is reported where the two
low-frequency points allow it but is not required, because it is unavailable
on exactly the spectra where it would matter most (the open arcs).

| criterion | why this system needs it |
|---|---|
| — | none beyond the floor; these sweeps were acquired one way, so no direction criterion applies |

## Approval

Approved by the ARIA/ATLANT-3D analysis owner, 19 August 2026, on the basis
that refusals are as valuable an output as numbers for this dataset.
