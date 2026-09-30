#!/usr/bin/env python3
"""Turn a pipeline result table into FIT and VERDICT artifacts.

Why this is a script and not a prompt. FIT and VERDICT records state what a
program computed. If a person writes them, the record is a memory of a
computation rather than the computation, and the two drift -- usually in the
direction the person hoped. So they are generated here, and `graph_gate.py` G7
fails any that lack an Attestation.

The input is a CSV, one row per measurement, from whatever pipeline produced
the fits. Column names are supplied by a mapping so this is not tied to one
analysis package; `--map` takes `artifact_field=csv_column` pairs, and
`--defaults` supplies values that are constant across the run.

Example (the ZnO/eis_suite case):

  python3 emit_artifacts.py results_750pass.csv \\
      --system zno --dataset cpt-zno-dataset-750pass \\
      --scan cpt-zno-scan-750pass --out artifacts \\
      --model 'Z = R_s + 1/(1/R_gb + Q (jw)^a)' \\
      --params R_s,R_gb,Q,alpha,tau \\
      --identifiability-test 'arc apex inside the window, -Z" falling on the low-f side' \\
      --misfit-label 'Median relative deviation over arc-bearing points' \\
      --weighting-calib cpt-zno-calib-weight-floor \\
      --misfit-calib cpt-zno-calib-misfit-metric \\
      --residual-calib cpt-zno-calib-residual-structure \\
      --attest 'eis_suite @ 2026-08-19, python run_series.py 750pass'

Nothing about the model is assumed. The identifiability test in particular is
a property of the MODEL, not of fitting: "the arc closes inside the window" is
the right test for a single-arc impedance model and meaningless for a
diffraction peak, so it is declared per run and printed in the VERDICT rather
than living in this file as a default. Earlier versions carried the ZnO
circuit's parameter list and its "arc-bearing points" wording as defaults;
those came out on 2026-09-30 when the kit was pointed at a second technique.

Stdlib only. Exit 0 on success, 2 on usage error.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path

# artifact field -> default CSV column name
DEFAULT_MAP = {
    "label": "label",
    "n_used": "n_kept",
    "n_total": "n_total",
    "misfit": "misfit",
    "noise": "noise",
    "identifiable": "identifiable",
    "resid_systematic": "resid_systematic",
    "resid_runs": "resid_runs",
    "resid_n": "resid_n",
    "on_bound": "on_bound",
    "verdict": "use",
    "reasons": "reasons",
}
# Columns an older pipeline may still write for a field. `arc_closed` was the
# identifiability column's name when the only model the kit had met was a
# single arc; every existing result table uses it, so it stays readable.
LEGACY_COLUMNS = {"identifiable": ["arc_closed"]}
# The identifiability test when none is declared. Deliberately generic: it is
# true of every model and specific to none, which is the point -- if a run
# wants the VERDICT to say what was actually tested, it says so.
IDENT_DEFAULT = "the feature that determines the parameter lies inside the measured range"
MISFIT_LABEL_DEFAULT = "Misfit statistic"

# These two patterns MUST stay identical to the pair in graph_gate.py, and the
# composition below MUST stay `permissive and not refusing`. The kit has been
# bitten twice by this pair: G4 composed them in the opposite order and read
# "not usable" as permitting, and these copies lacked word boundaries, so
# "unusable" matched PERMISSIVE via the substring "usable" and emitted a
# *permitted* verdict for a refusal. `tests/test_routing.py` asserts both files
# agree, phrase by phrase.
PERMISSIVE = re.compile(r"\b(usable|trustworthy|permitted)\b", re.I)
REFUSING = re.compile(r"\b(not usable|refused|unusable|lower bound)\b", re.I)


LEDGER = "emitted.json"


def write_ledger(out: Path, a, rows, emitted: list) -> None:
    """Record what this emit produced, keyed by DATASET, into `emitted.json`.

    This is the input side of gate G8. The tree alone cannot answer "did every
    measurement arrive?" -- 27 artifacts are exactly as well-formed as 54, and
    on the run that motivated this, the gates passed on half the data. So the
    emitting step states its own count and ids, and the gate compares.

    Entries are keyed by dataset AND by source table, and the dataset's `ids`
    are the UNION over its sources.

    The previous version wrote `doc[dataset] = {... ids: this emit's ids}`,
    which silently discarded the ids of every earlier emit from the same
    DATASET. That is not an exotic case: a single fit commonly yields more than
    one parameter, FIT and VERDICT pair one-to-one (G8), so each parameter needs
    its own emit -- and the second one erased the first from the ledger. Found
    by an independent field test on synchrotron XRD (Pd-Si, Zenodo 20798555,
    2026-09-22), which then deleted all 150 artifacts of the run's PRIMARY
    parameter and watched graph_gate report PASS. That is the same silent loss
    G8 was added to prevent, one level up, inside the mechanism meant to prevent
    it.

    Re-emitting the same source replaces only that source's entry, so a re-run
    is idempotent rather than doubling the counts.
    """
    import json

    path = out / LEDGER
    doc = {}
    if path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            doc = {}

    entry = doc.get(a.dataset) or {}
    emits = dict(entry.get("emits") or {})
    # migrate a ledger written by the pre-fix version, which had no `emits`
    if not emits and entry.get("ids"):
        emits[entry.get("source", "<unknown>")] = dict(
            date=entry.get("date", ""),
            n_measurements=entry.get("n_measurements", len(entry["ids"]) // 2),
            attest=entry.get("attest", ""), ids=sorted(entry["ids"]))

    emits[str(a.csv)] = dict(date=a.date, n_measurements=len(rows),
                             attest=a.attest, ids=sorted(emitted))

    all_ids = sorted({i for e in emits.values() for i in e["ids"]})
    doc[a.dataset] = dict(
        system=a.system, scan=a.scan, sources=sorted(emits),
        n_measurements=sum(e["n_measurements"] for e in emits.values()),
        emits=emits, ids=all_ids)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-+", "-", s)


def num(row, col, default=float("nan")):
    v = (row.get(col) or "").strip()
    if v in ("", "nan", "None"):
        return default
    try:
        return float(v)
    except ValueError:
        return default


def truthy(row, col):
    return (row.get(col) or "").strip().lower() in ("true", "1", "yes")


def pct(x, digits=1):
    """Render a fraction as a percentage without destroying small thresholds.

    `f"{x*100:.0f}%"` printed the calibrated gates 0.008 and 0.006 both as
    "1%", and 0.003 as "0%" -- a generated VERDICT misreporting the very
    threshold it was judged against, and "> 0%" reads as no threshold at all.
    Keep enough decimals that the value survives the round trip.
    """
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "—"
    v = x * 100.0
    if v == 0:
        return "0%"
    d = digits
    while d < 6 and round(v, d) == 0:
        d += 1
    # drop trailing zeros so 15.0% stays "15%"
    return f"{round(v, d):g}%"


def extra_rows(row, a) -> str:
    """Extra Evidence rows from --extra-criterion, one per flag.

    Returns "" when none were given, so the table is byte-identical to before
    for every existing caller.
    """
    out = []
    for spec in getattr(a, "extra_criterion", []) or []:
        parts = [s.strip() for s in spec.split("|")]
        if len(parts) != 4:
            raise SystemExit(
                f"--extra-criterion needs 4 |-separated fields "
                f"(LABEL|VALUE|THRESHOLD|CALIB-ID), got {len(parts)}: {spec!r}")
        label, value, thresh, calib = parts
        # a CSV column if one matches, else the literal text
        if value in row:
            v = (row.get(value) or "").strip() or "—"
        else:
            v = value
        out.append(f"| {label} | {v} | {thresh} | `{calib}` |")
    return "\n".join(out)


def toc(sections):
    """The `<!-- toc -->` block `cfs validate` requires, in its own format.

    The emitter never wrote one. The shipped examples have one because they
    were hand-fixed with `cfs toc`, so the kit's two validation layers
    disagreed about the emitter's own output: `graph_gate.py` said PASS on a
    tree that `cfs validate` failed with one error per generated artifact
    ("Document has headings but no Table of Contents section"). And there was
    no legitimate way out -- G7 forbids hand-editing a script-generated record,
    which is exactly what running `cfs toc` on one would be. Found by the Pd-Si
    field test, 2026-09-22.
    """
    links = "\n".join(f"- [{s}](#{s.lower().replace(' ', '-')})"
                      for s in sections)
    return f"\n<!-- toc -->\n\n{links}\n\n<!-- /toc -->\n"


def fmt(x, unit="", digits=4):
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "—"
    if isinstance(x, float):
        if x != 0 and (abs(x) >= 1e4 or abs(x) < 1e-3):
            return f"{x:.{digits}g}{unit}"
        return f"{x:.{digits}g}{unit}"
    return f"{x}{unit}"


def fit_doc(row, a, cmap, params) -> str:
    label = row[cmap["label"]]
    slug = slugify(label)
    n_used, n_tot = num(row, cmap["n_used"]), num(row, cmap["n_total"])
    dropped = ""
    if math.isfinite(n_used) and math.isfinite(n_tot):
        dropped = (f"**{int(n_used)} of {int(n_tot)} points used.** "
                   f"{int(n_tot - n_used)} excluded by "
                   f"`{a.scan}`.")
    bound = (row.get(cmap["on_bound"]) or "").strip()
    rows = []
    for p in params:
        v = num(row, p)
        rows.append(f"| {p} | {fmt(v)} | — | "
                    f"{'**yes**' if p in bound else 'no'} |")
    return f"""---
status: complete
date: {a.date}
---

# Fit — {label}
{toc(["Measurement", "Model", "Weighting", "Parameters", "Attestation"])}
**ID**: `cpt-{a.system}-fit-{slug}`

## Measurement

`{label}` from `{a.dataset}`, after `{a.scan}`.

{dropped}

## Model

```
{a.model}
```

## Weighting

{a.weighting}

Licensed by `{a.weighting_calib}`.

## Parameters

| parameter | value | uncertainty | on bound? |
|---|---|---|---|
{chr(10).join(rows)}

{a.misfit_label}: **{pct(num(row, cmap['misfit']))}**.
{'A parameter resting on a bound is not determined by the data.' if bound else ''}

## Attestation

{a.attest}
"""


def verdict_doc(row, a, cmap) -> str:
    label = row[cmap["label"]]
    slug = slugify(label)
    call_raw = (row.get(cmap["verdict"]) or "").strip()
    reasons = (row.get(cmap["reasons"]) or "").strip()
    permitted = bool(PERMISSIVE.search(call_raw)) and not REFUSING.search(call_raw)
    mis, noise = num(row, cmap["misfit"]), num(row, cmap["noise"])
    identifiable = truthy(row, cmap["identifiable"])
    systematic = truthy(row, cmap["resid_systematic"])
    runs, rn = num(row, cmap["resid_runs"]), num(row, cmap["resid_n"])

    resid_txt = (f"systematic ({int(runs)} run(s) over {int(rn)} points)"
                 if systematic and math.isfinite(runs)
                 else "random" if math.isfinite(runs) else "not assessed")
    ident_txt = (f"test passed: {a.identifiability_test}" if identifiable
                 else f"**test failed: {a.identifiability_test}**")

    # biased vs imprecise -- the distinction the rules require on a refusal
    if permitted:
        call = (f"**Usable.** {call_raw}."
                + (f" Recorded caveat: {reasons}." if reasons else ""))
    else:
        kind = ("**biased** — the residual is systematic, so the model does not "
                "describe the data's shape; no uncertainty covers this"
                if systematic else
                "**imprecise** — the residual is random, so the model is not "
                "contradicted; there is not enough signal to determine the "
                "parameter")
        call = (f"**Refused.** {call_raw}"
                + (f" ({reasons})" if reasons else "") + f".\n\nThe parameter is "
                f"{kind}.")

    return f"""---
status: {'permitted' if permitted else 'refused'}
date: {a.date}
---

# Verdict — {label}
{toc(["Fit", "Evidence", "Call", "Attestation"])}
**ID**: `cpt-{a.system}-verdict-{slug}`

## Fit

`cpt-{a.system}-fit-{slug}`.

## Evidence

| criterion | measured | threshold | licensed by |
|---|---|---|---|
| identifiability | {ident_txt} | the declared test must pass | `{a.identifiability_calib}` |
| misfit | {pct(mis)} | < {pct(a.misfit_max)} | `{a.misfit_calib}` |
| residual structure | {resid_txt} | {a.resid_rule} | `{a.residual_calib}` |
| noise | {pct(noise)} | < {pct(a.noise_max)} | `{a.noise_calib}` |
| instrument range | see `{a.dataset}` | dataset-declared trusted range | `{a.range_calib}` |
{extra_rows(row, a)}

## Call

{call}

## Attestation

{a.attest}
"""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv")
    p.add_argument("--system", required=True)
    p.add_argument("--dataset", required=True)
    p.add_argument("--scan", required=True)
    p.add_argument("--out", default="artifacts")
    p.add_argument("--model", required=True)
    p.add_argument("--weighting", default="See the pipeline's weighting model.")
    p.add_argument("--weighting-calib", required=True)
    p.add_argument("--misfit-calib", required=True)
    p.add_argument("--residual-calib", required=True)
    p.add_argument("--attest", required=True)
    p.add_argument("--date", default="")
    p.add_argument("--params", required=True,
                   help="comma-separated CSV columns holding the fitted "
                        "parameters, in the order the FIT should list them. "
                        "Required: a default list would be one model's, and "
                        "the kit assumes no model")
    p.add_argument("--identifiability-test", default=IDENT_DEFAULT,
                   help="the test behind the identifiability row, verbatim, "
                        "as the VERDICT should print it. It belongs to the "
                        "model: 'arc apex inside the window' for a single "
                        "arc, 'peak maximum and both half-maxima inside the "
                        "scan' for a diffraction line. The column it reads "
                        "is --map identifiable=<col>")
    p.add_argument("--misfit-label", default=MISFIT_LABEL_DEFAULT,
                   help="what the misfit column measures, as the FIT should "
                        "print it (default: %(default)r)")
    p.add_argument("--map", nargs="*", default=[],
                   help="artifact_field=csv_column overrides")
    p.add_argument("--misfit-max", type=float, default=0.15)
    p.add_argument("--resid-gate", type=float, default=0.10)
    p.add_argument("--noise-max", type=float, default=0.35)
    # Which calibration licenses which criterion. These used to be hard-wired
    # to --misfit-calib and --weighting-calib, which is wrong for any pipeline
    # whose window/identifiability work is a separate calibration: the Evidence
    # table then cited a real artifact that had not scored that criterion, and
    # G2 passed because the id resolved.
    p.add_argument("--identifiability-calib", default="",
                   help="licenses the identifiability row "
                        "(default: --misfit-calib)")
    p.add_argument("--range-calib", default="",
                   help="licenses the instrument-range row "
                        "(default: --weighting-calib)")
    p.add_argument("--noise-calib", default="",
                   help="licenses the noise row (default: --misfit-calib)")
    # D4: the Evidence table was a fixed five rows with no way to add one.
    # USAGE said "edit artifacts/VERDICT/rules.md if your domain needs a sixth"
    # -- but rules.md is in graph_gate's SKIP set and never parsed, and
    # REQUIRED_EVIDENCE is a hard-coded list, so editing it changed nothing.
    # The documented extension path was inert, and the field test's two extra
    # criteria ended up in free-text `reasons`: thresholds with no calibration,
    # which is what carrying rule 2 forbids. An extra row here is cited like
    # any other and is therefore gated by G2.
    p.add_argument("--extra-criterion", action="append", default=[],
                   metavar="LABEL|VALUE|THRESHOLD|CALIB-ID",
                   help="append a row to every VERDICT's Evidence table. "
                        "VALUE is a CSV column name if one matches, else "
                        "literal text. Repeatable. The five built-in criteria "
                        "are a minimum, not a maximum.")
    p.add_argument("--resid-rule", default="",
                   help="the deployed residual-structure rule, verbatim "
                        "(default: 'systematic and misfit > <resid-gate>'). "
                        "A conjunction of other statistics cannot be written "
                        "in the default phrasing, and the rule that is "
                        "calibrated must be the rule that is printed.")
    a = p.parse_args()

    if not a.date:
        # no clock call: take it from the file's own mtime so runs are
        # reproducible from inputs alone
        import datetime
        a.date = datetime.date.fromtimestamp(
            Path(a.csv).stat().st_mtime).isoformat()

    # default each criterion's licensing calibration to the old behaviour
    a.identifiability_calib = a.identifiability_calib or a.misfit_calib
    a.range_calib = a.range_calib or a.weighting_calib
    a.noise_calib = a.noise_calib or a.misfit_calib
    a.resid_rule = a.resid_rule or f"systematic and misfit > {pct(a.resid_gate)}"

    cmap = dict(DEFAULT_MAP)
    for kv in a.map:
        if "=" not in kv:
            print(f"bad --map entry: {kv}")
            return 2
        k, _, v = kv.partition("=")
        cmap[k] = v
    params = [x.strip() for x in a.params.split(",") if x.strip()]

    with open(a.csv, newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = [r for r in reader
                if (r.get("ok") or "True").strip().lower() in ("true", "1", "yes")]
    if not rows:
        print("no usable rows in the input table")
        return 2

    # a field whose default column is absent falls back to its legacy name
    for field, olds in LEGACY_COLUMNS.items():
        if cmap[field] not in header:
            for old in olds:
                if old in header:
                    cmap[field] = old
                    break
    absent = [(f, c) for f, c in cmap.items()
              if c not in header and f not in ("resid_runs", "resid_n")]
    absent += [(f"param {x}", x) for x in params if x not in header]
    if absent:
        print("error: the table has no column for: "
              + ", ".join(f"{f} ({c})" for f, c in absent)
              + ". Name the column with --map field=column.", file=sys.stderr)
        return 2

    out = Path(a.out)
    (out / "FIT").mkdir(parents=True, exist_ok=True)
    (out / "VERDICT").mkdir(parents=True, exist_ok=True)

    # A slug collides when two measurements share a label. That happens across
    # DATASETS whose labels are conditions rather than sample ids -- the ZnO
    # cohorts both label spectra "150C-10.0mm/s-dark" -- and the second emit
    # then overwrites the first without a word, leaving an artifact tree that
    # looks complete and holds half the run. Refuse instead: silent loss is the
    # failure this kit exists to prevent, and it must not be committed by the
    # kit's own script.
    seen: dict = {}
    for r in rows:
        slug = slugify(r[cmap["label"]])
        if slug in seen:
            print(f"error: two measurements slugify to {slug!r} "
                  f"({seen[slug]!r} and {r[cmap['label']]!r}). Artifact IDs "
                  f"must be unique within a tree.\n"
                  f"Give the label a per-dataset prefix, or emit each dataset "
                  f"under its own --out.", file=sys.stderr)
            return 2
        seen[slug] = r[cmap["label"]]

    n_perm = 0
    emitted = []
    for r in rows:
        slug = slugify(r[cmap["label"]])
        for kind, doc in (("FIT", fit_doc(r, a, cmap, params)),
                          ("VERDICT", verdict_doc(r, a, cmap))):
            p = out / kind / f"{slug}.md"
            # Also refuse to clobber a file left by an EARLIER emit into the
            # same tree, which is how the cohorts collided in practice.
            if p.exists() and p.read_text(encoding="utf-8") != doc:
                print(f"error: {p} already exists with different content. "
                      f"Another dataset in this tree uses the id "
                      f"cpt-{a.system}-{kind.lower()}-{slug}.", file=sys.stderr)
                return 2
            p.write_text(doc, encoding="utf-8")
            emitted.append(f"cpt-{a.system}-{kind.lower()}-{slug}")
        n_perm += verdict_doc(r, a, cmap).startswith("---\nstatus: permitted")

    # Declare what this run emitted, so a later gate can check the tree against
    # the intent rather than only for internal consistency. Without this the
    # tree is only ever checked for being well-formed, and half a run is
    # perfectly well-formed.
    write_ledger(out, a, rows, emitted)

    print(f"emit_artifacts: {len(rows)} measurements")
    print(f"  FIT      -> {out/'FIT'}")
    print(f"  VERDICT  -> {out/'VERDICT'}  ({n_perm} permitted, "
          f"{len(rows)-n_perm} refused)")
    print(f"\nNow run: python3 graph_gate.py {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
