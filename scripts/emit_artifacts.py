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
      --weighting-calib cpt-zno-calib-weight-floor \\
      --misfit-calib cpt-zno-calib-misfit-metric \\
      --residual-calib cpt-zno-calib-residual-structure \\
      --attest 'eis_suite @ 2026-08-19, python run_series.py 750pass'

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
    "closed": "arc_closed",
    "resid_systematic": "resid_systematic",
    "resid_runs": "resid_runs",
    "resid_n": "resid_n",
    "on_bound": "on_bound",
    "verdict": "use",
    "reasons": "reasons",
}
# free-form parameter columns are everything else the user names
PARAM_DEFAULT = ["R_s", "R_gb", "Q", "alpha", "tau"]

PERMISSIVE = re.compile(r"trustworthy|usable|permitted", re.I)
REFUSING = re.compile(r"not usable|refused|lower bound", re.I)


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

Median relative deviation over arc-bearing points: **{num(row, cmap['misfit'])*100:.1f}%**.
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
    closed = truthy(row, cmap["closed"])
    systematic = truthy(row, cmap["resid_systematic"])
    runs, rn = num(row, cmap["resid_runs"]), num(row, cmap["resid_n"])

    resid_txt = (f"systematic ({int(runs)} run(s) over {int(rn)} arc points)"
                 if systematic and math.isfinite(runs)
                 else "random" if math.isfinite(runs) else "not assessed")

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

**ID**: `cpt-{a.system}-verdict-{slug}`

## Fit

`cpt-{a.system}-fit-{slug}`.

## Evidence

| criterion | measured | threshold | licensed by |
|---|---|---|---|
| identifiability | {'feature resolved inside the measured range' if closed else '**not resolved inside the measured range**'} | must resolve inside the window | `{a.misfit_calib}` |
| misfit | {mis*100:.1f}% | < {a.misfit_max*100:.0f}% | `{a.misfit_calib}` |
| residual structure | {resid_txt} | systematic and misfit > {a.resid_gate*100:.0f}% | `{a.residual_calib}` |
| noise | {noise*100:.1f}% | < {a.noise_max*100:.0f}% | `{a.misfit_calib}` |
| instrument range | see `{a.dataset}` | dataset-declared trusted range | `{a.weighting_calib}` |

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
    p.add_argument("--params", default=",".join(PARAM_DEFAULT))
    p.add_argument("--map", nargs="*", default=[],
                   help="artifact_field=csv_column overrides")
    p.add_argument("--misfit-max", type=float, default=0.15)
    p.add_argument("--resid-gate", type=float, default=0.10)
    p.add_argument("--noise-max", type=float, default=0.35)
    a = p.parse_args()

    if not a.date:
        # no clock call: take it from the file's own mtime so runs are
        # reproducible from inputs alone
        import datetime
        a.date = datetime.date.fromtimestamp(
            Path(a.csv).stat().st_mtime).isoformat()

    cmap = dict(DEFAULT_MAP)
    for kv in a.map:
        if "=" not in kv:
            print(f"bad --map entry: {kv}")
            return 2
        k, _, v = kv.partition("=")
        cmap[k] = v
    params = [x.strip() for x in a.params.split(",") if x.strip()]

    with open(a.csv, newline="") as fh:
        rows = [r for r in csv.DictReader(fh)
                if (r.get("ok") or "True").strip().lower() in ("true", "1", "yes")]
    if not rows:
        print("no usable rows in the input table")
        return 2

    out = Path(a.out)
    (out / "FIT").mkdir(parents=True, exist_ok=True)
    (out / "VERDICT").mkdir(parents=True, exist_ok=True)

    n_perm = 0
    for r in rows:
        slug = slugify(r[cmap["label"]])
        (out / "FIT" / f"{slug}.md").write_text(fit_doc(r, a, cmap, params),
                                                encoding="utf-8")
        vd = verdict_doc(r, a, cmap)
        (out / "VERDICT" / f"{slug}.md").write_text(vd, encoding="utf-8")
        n_perm += vd.startswith("---\nstatus: permitted")

    print(f"emit_artifacts: {len(rows)} measurements")
    print(f"  FIT      -> {out/'FIT'}")
    print(f"  VERDICT  -> {out/'VERDICT'}  ({n_perm} permitted, "
          f"{len(rows)-n_perm} refused)")
    print(f"\nNow run: python3 graph_gate.py {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
