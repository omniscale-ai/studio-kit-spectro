#!/usr/bin/env python3
"""G9: a supported trend may not run along an axis declared SYNTHESIS.

Regression home for the second defect found by the Pd-Si XRD field test
(2026-09-22). A deliberately planted claim -- "silicon suppresses grain growth,
-2.5 nm per at.% Si, R2 = 0.98" -- passed all eight gates, although:

  * Si content is a declared SYNTHESIS axis: every value is a different film;
  * the one contradicting film had been dropped;
  * it was confounded with sample holder AND with scan step.

Every one of those facts was already written in the artifact tree. The DATASET
declared the axis SYNTHESIS, G5 enforced that it be declared -- and nothing
connected the declaration to a FINDING that used it. The rule existed in
FINDING/rules.md, in the template's confound table, and in G4's own docstring
as the failure G4 prevents. It was enforced nowhere.

The important property of the case, and the reason this needs its own test:
**the supporting verdicts are all sound**. Each is a good measurement, so no
verdict-level check can help and G4 cannot fire. The failure is one level up.

Stdlib only. Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import synth  # noqa: E402

fails = []


def ok(m):
    print(f"  ok   {m}")


def bad(m):
    print(f"  FAIL {m}")
    fails.append(m)


def check(c, m):
    ok(m) if c else bad(m)


MEAS = f"`injected noise level` in `{synth.DATASET_ID}`"
SYNTH_AXIS = f"`arm` in `{synth.DATASET_ID}`"


def build(td: Path):
    """A tree whose permitted verdicts are all genuinely good measurements."""
    art = synth.build_tree(td)
    rows = synth.ladder([0.005], n_per=6, arms=("good",))
    csvp = synth.write_table(td / "results.csv", rows)
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "emit_artifacts.py"), str(csvp),
         "--system", synth.SYSTEM, "--dataset", synth.DATASET_ID,
         "--scan", synth.SCAN_ID, "--out", str(art), "--model", "Z = R_s + arc",
         "--weighting", "proportional",
         "--weighting-calib", synth.CALIBS["weight"],
         "--misfit-calib", synth.CALIBS["misfit"],
         "--residual-calib", synth.CALIBS["residual"],
         "--params", "R_s,R_ct,alpha", "--attest", "tests/test_axis_kind.py"],
        capture_output=True, text=True)
    if r.returncode != 0:
        bad(f"emit failed: {r.stderr.strip()[:200]}")
    ids = []
    for p in sorted((art / "VERDICT").glob("*.md")):
        if p.name in {"template.md", "rules.md", "checklist.md"}:
            continue
        t = p.read_text(encoding="utf-8")
        if t.startswith("---\nstatus: permitted"):
            ids.append(next(l for l in t.splitlines()
                            if l.startswith("**ID**")).split("`")[1])
    return art, ids


def gate(art):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "graph_gate.py"),
                        str(art)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def case(name, status, axis, expect_pass, expect_gate=None):
    with tempfile.TemporaryDirectory() as td:
        art, ids = build(Path(td))
        if not ids:
            bad(f"{name}: no permitted verdicts to build a finding on")
            return
        synth.write_finding(art, "trend", status, ids,
                            "R_ct falls by 2.5 units per unit of the axis",
                            axis=axis)
        rc, out = gate(art)
        if expect_pass:
            check(rc == 0, f"{name} -> PASS")
            if rc != 0:
                print("        " + out.strip().splitlines()[-1][:110])
        else:
            hit = expect_gate is None or expect_gate in out
            check(rc != 0 and hit, f"{name} -> FAIL ({expect_gate or 'any'})")


print("\n=== 1. the field test's case: a rate law along a SYNTHESIS axis ===")
print("       (every supporting verdict is permitted, so G4 cannot fire)")
case("supported claim along a SYNTHESIS axis", "supported", SYNTH_AXIS,
     expect_pass=False, expect_gate="G9")

print("\n=== 2. the same claim, legitimately stated ===")
case("supported claim along a MEASUREMENT axis", "supported", MEAS,
     expect_pass=True)
case("same SYNTHESIS claim marked retracted", "retracted", SYNTH_AXIS,
     expect_pass=True)
case("a claim that is not a trend at all ('none')", "supported", "none",
     expect_pass=True)
case("'none' written with backticks and prose", "supported",
     "`none` — a magnitude over a population, not a trend.", expect_pass=True)

print("\n=== 3. the declaration must actually resolve ===")
case("Claimed Axis left empty", "supported", "", expect_pass=False,
     expect_gate="G9")
case("axis named but no DATASET", "supported", "`arm`", expect_pass=False,
     expect_gate="G9")
case("axis absent from the DATASET's table", "supported",
     f"`laser fluence` in `{synth.DATASET_ID}`", expect_pass=False,
     expect_gate="G9")
case("DATASET that does not exist", "supported",
     "`arm` in `cpt-synth-dataset-nosuch`", expect_pass=False,
     expect_gate="G9")

print("\n=== 4. prose after the declaration is not parsed as axis names ===")
case("declaration followed by backticked prose", "supported",
     MEAS + "\n\nThe rate law is `R_ct = a + b*x`, and the status here is\n"
            "`supported` deliberately.", expect_pass=True)

print()
if fails:
    print(f"FAIL — {len(fails)} check(s) failed")
    sys.exit(1)
print("PASS — a supported claim cannot run along a synthesis axis unnoticed")
