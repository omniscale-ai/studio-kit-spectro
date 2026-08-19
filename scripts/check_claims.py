#!/usr/bin/env python3
"""Do the numbers quoted in this kit's example artifacts match their provenance?

They went stale once: tightening the verdict criteria upstream silently
invalidated numbers in a shipped artifact and a shipped report, and nothing
noticed. This closes that loop.

HOW IT MUST WORK, and how a first version got it wrong. The check has to READ
THE NUMBER OUT OF THE ARTIFACT and compare it with the value recomputed from
the shipped tables. A first version instead compared a copy of each number kept
in this script against the recomputed value -- which passes happily while the
artifact says something different, i.e. it could not detect the one failure it
exists for. Every claim below therefore carries a regex that extracts the value
from the artifact text.

Provenance lives in `tests/provenance/`; the kit ships it rather than referring
to it, on its own principle that an artifact quoting a number ships with the
evidence for that number. Standard library only -- no dependency on the analysis
package that produced the tables, and none on numpy: this must run for someone
who has only the kit and a bare Python.

  python3 scripts/check_claims.py [--verbose]
Exit: 0 all claims current, 1 drift found, 2 setup error.
"""

from __future__ import annotations

import csv
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = os.path.join(ROOT, "artifacts")
DATA = os.path.join(ROOT, "tests", "provenance")


TOL = 0.02          # 2% relative for measured quantities; counts must match


def load(name):
    with open(os.path.join(DATA, f"results_{name}.csv")) as fh:
        return [r for r in csv.DictReader(fh) if r.get("ok") == "True"]


def fnum(r, k):
    v = (r.get(k) or "").strip()
    if v in ("", "nan", "None"):
        return float("nan")
    try:
        return float(v)
    except ValueError:
        return float("nan")


def trusted(rows):
    return [r for r in rows if r["use"] == "R_gb trustworthy"]


def c_eff(r):
    """C = (R^(1-a) Q)^(1/a) in pF, inlined to keep this dependency-free."""
    R, Q, a = fnum(r, "R_gb"), fnum(r, "Q"), fnum(r, "alpha")
    try:
        return float((R ** (1 - a) * Q) ** (1.0 / a)) * 1e12
    except (ValueError, ZeroDivisionError, OverflowError):
        return float("nan")


def median_dark(rows, T):
    v = [fnum(r, "R_gb") / 1e6 for r in trusted(rows)
         if abs(fnum(r, "cond_temp_C") - T) < 0.5 and r["cond_illum"] == "dark"]
    return float(statistics.median(v)) if v else float("nan")


# ---------------------------------------------------------------------------
# each claim: artifact, description, regex capturing the quoted number, actual
# ---------------------------------------------------------------------------
def claims():
    c750, ccs = load("750pass"), load("cseries")
    out = []

    def add(path, desc, pattern, actual, integer=False):
        out.append(dict(path=path, desc=desc, pattern=pattern, actual=actual,
                        integer=integer))

    # --- the permitted spectrum -------------------------------------------
    r = next(r for r in c750 if r["label"] == "200C-5.0mm/s-dark")
    v = "VERDICT/examples/example-zno-200c5-dark.md"
    add(v, "misfit", r"\|\s*misfit\s*\|\s*([\d.]+)%", fnum(r, "misfit") * 100)
    add(v, "noise", r"\|\s*noise\s*\|\s*([\d.]+)%", fnum(r, "noise") * 100)
    add(v, "arc points in runs test", r"over (\d+) arc points",
        fnum(r, "resid_n"), integer=True)
    f = "FIT/examples/example-zno-200c5-dark.md"
    add(f, "R_gb / MOhm", r"\|\s*R_gb\s*\|\s*([\d.]+)\s*M", fnum(r, "R_gb") / 1e6)
    add(f, "alpha", r"\|\s*α\s*\|\s*([\d.]+)\s*\|", fnum(r, "alpha"))
    add(f, "measured R_dc / MOhm", r"measured R_dc of ([\d.]+)\s*M",
        fnum(r, "R_dc") / 1e6)
    add(f, "points used", r"\*\*(\d+) of \d+ points used", fnum(r, "n_kept"),
        integer=True)
    add(f, "n_eff", r"Kish\)\s*\*\*([\d.]+) of", fnum(r, "n_eff"))

    # --- the refused spectrum ---------------------------------------------
    r = next(r for r in ccs if r["label"] == "250C-5.0mm/s-dark")
    v = "VERDICT/examples/example-zno-250c5-dark.md"
    add(v, "misfit", r"\*\*([\d.]+)%\*\*", fnum(r, "misfit") * 100)
    add(v, "noise", r"\|\s*noise\s*\|\s*([\d.]+)%", fnum(r, "noise") * 100)
    f = "FIT/examples/example-zno-250c5-dark.md"
    add(f, "R_gb / MOhm", r"\|\s*R_gb\s*\|\s*\**([\d.]+)\**\s*M",
        fnum(r, "R_gb") / 1e6)
    add(f, "alpha", r"\|\s*α\s*\|\s*([\d.]+)\s*\|", fnum(r, "alpha"))
    add(f, "points used", r"\*\*(\d+) of \d+ points used", fnum(r, "n_kept"),
        integer=True)
    add(f, "n_eff", r"Effective sample size ([\d.]+) of", fnum(r, "n_eff"))

    # --- effective capacitance --------------------------------------------
    p = "FINDING/examples/example-effective-capacitance.md"
    for name, rows, lo_pat, hi_pat in (
            ("750-pass", c750, r"(\d+)–\d+ pF in the 750-pass set",
             r"\d+–(\d+) pF in the 750-pass set"),
            ("C-series", ccs, r"(\d+)–\d+ pF\s*\n?\s*in the C-series",
             r"\d+–(\d+) pF\s*\n?\s*in the C-series")):
        vals = [c_eff(r) for r in trusted(rows) if "dark" in r["label"]]
        vals = [x for x in vals if math.isfinite(x)]
        add(p, f"{name} dark C_eff low / pF", lo_pat, min(vals))
        add(p, f"{name} dark C_eff high / pF", hi_pat, max(vals))
    add(p, "permitted verdicts, 750-pass", r"(\d+) permitted verdicts in the",
        len(trusted(c750)), integer=True)
    add(p, "permitted verdicts, C-series", r"and (\d+) in the C-series",
        len(trusted(ccs)), integer=True)

    # --- the retraction ----------------------------------------------------
    p = "FINDING/examples/example-activation-energy.md"
    add(p, "750-pass R_gb dark at 150 C",
        r"750-pass, R_gb \| ([\d.]+) MΩ", median_dark(c750, 150))
    add(p, "750-pass R_gb dark at 200 C",
        r"750-pass, R_gb \| [\d.]+ MΩ \(n=\d\) \| ([\d.]+)",
        median_dark(c750, 200))
    add(p, "750-pass R_gb dark at 250 C",
        r"750-pass, R_gb \| [\d.]+ MΩ \(n=\d\) \| [\d.]+ \(n=\d\) \| ([\d.]+)",
        median_dark(c750, 250))
    add(p, "C-series R_gb dark at 150 C",
        r"C-series, R_gb \| ([\d.]+) MΩ", median_dark(ccs, 150))
    n200 = [r for r in trusted(ccs)
            if abs(fnum(r, "cond_temp_C") - 200) < 0.5
            and r["cond_illum"] == "dark"]
    add(p, "C-series usable dark spectra at 200 C",
        r"has (one|\d+) usable dark spectrum at 150 °C, (none|\d+) at 200",
        len(n200), integer=True)
    return out


WORDS = {"none": 0, "one": 1, "two": 2, "three": 3}


def main() -> int:
    for d in (KIT, DATA):
        if not os.path.isdir(d):
            print(f"not found: {d}")
            return 2
    verbose = "--verbose" in sys.argv

    bad, checked = [], 0
    for c in claims():
        checked += 1
        full = os.path.join(KIT, c["path"])
        if not os.path.exists(full):
            bad.append((c, None, "artifact missing"))
            continue
        text = open(full, encoding="utf-8").read()
        m = re.search(c["pattern"], text)
        if not m:
            bad.append((c, None, "claim not found in artifact — the artifact "
                                 "was reworded, so this check no longer "
                                 "verifies it"))
            continue
        raw = m.group(m.lastindex or 1)
        quoted = float(WORDS.get(raw.lower(), raw)) if not raw.replace(
            ".", "", 1).isdigit() else float(raw)
        actual = c["actual"]
        if not math.isfinite(actual):
            bad.append((c, quoted, "no longer computable from provenance"))
            continue
        ok = (abs(actual - quoted) <= 1 if c["integer"]
              else abs(actual - quoted) <= TOL * max(abs(quoted), 1e-12))
        if not ok:
            bad.append((c, quoted, "drifted"))
        elif verbose:
            print(f"  ok   {c['path']:<50s} {c['desc']:<34s} "
                  f"{quoted} ~ {actual:.4g}")

    print(f"check_claims: {checked} claims read from artifacts and checked "
          f"against tests/provenance/")
    if bad:
        print()
        for c, quoted, why in bad:
            a = c["actual"]
            av = f"{a:.4g}" if isinstance(a, float) and math.isfinite(a) else a
            q = "—" if quoted is None else quoted
            print(f"  [{why}] {c['path']}\n        {c['desc']}: artifact says "
                  f"{q}, provenance gives {av}")
        print(f"\nFAIL — {len(bad)} stale or unverifiable claim(s).")
        return 1
    print("\nPASS — every quoted number matches its provenance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
