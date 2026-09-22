#!/usr/bin/env python3
"""Noise test: give the kit noisy data and check it says so, correctly.

The kit ships no fitter, so this does not test an optimiser. What it tests is
the thing the kit actually owns: given a result table, does the chain route
each measurement to the right *kind* of answer, and does a refusal stop
propagating into a claim?

Four arms with truth known by construction (see `tests/synth.py`):

  right model, low noise    -> PERMITTED
  right model, high noise   -> REFUSED as IMPRECISE   (widen the uncertainty)
  wrong model, any noise    -> REFUSED as BIASED      (change the model)
  truncated arc, low misfit -> REFUSED                (a beautiful fit that
                                                       determines nothing)

The third and fourth arms are the ones worth having. "Low noise with a poor fit
means a wrong model, not bad data" is only useful if the pipeline acts on it,
and identifiability is not fit quality -- a truncated arc can be fitted
beautifully over the points that were measured. Both were real failures in the
work this kit came from.

A companion check closes the loop: a FINDING built on the high-noise end must
fail the gate. Noise that is correctly labelled but still reaches a conclusion
has not been handled.

Stdlib only. Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import synth  # noqa: E402

fails = []


def ok(msg):
    print(f"  ok   {msg}")


def bad(msg):
    print(f"  FAIL {msg}")
    fails.append(msg)


def check(cond, msg):
    ok(msg) if cond else bad(msg)


spec = importlib.util.spec_from_file_location(
    "_kit_emit", ROOT / "scripts" / "emit_artifacts.py")
emit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emit)

# 0.13 sits deliberately on the misfit gate, so the ladder has a partial rung
# rather than stepping straight from all-permitted to none: a monotonicity test
# over a cliff would pass even if the criterion were binary in the wrong place.
LEVELS = [0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.13, 0.20, 0.30]
N_PER = 8
RIGHT_MODEL = ("good", "noisy")


def build(tmp: Path, rows):
    art = synth.build_tree(tmp)
    csv_path = synth.write_table(tmp / "results.csv", rows)
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "emit_artifacts.py"),
         str(csv_path), "--system", synth.SYSTEM,
         "--dataset", synth.DATASET_ID, "--scan", synth.SCAN_ID,
         "--out", str(art),
         "--model", "Z(w) = R_s + 1/(1/R_ct + Q (jw)^alpha)",
         "--weighting", "proportional with a 0.2% floor",
         "--weighting-calib", synth.CALIBS["weight"],
         "--misfit-calib", synth.CALIBS["misfit"],
         "--residual-calib", synth.CALIBS["residual"],
         "--identifiability-calib", synth.CALIBS["window"],
         "--range-calib", synth.CALIBS["window"],
         "--noise-calib", synth.CALIBS["noise"],
         "--resid-rule", f"systematic AND misfit > "
                         f"{synth.RESID_GATE*100:g}%",
         "--params", "R_s,R_ct,alpha",
         "--attest", "tests/test_noise.py"],
        capture_output=True, text=True)
    if r.returncode != 0:
        bad(f"emit failed: {r.stderr.strip()[:300]}")
    return art


def read_verdicts(art: Path, rows):
    """label -> (permitted, kind, text) for every emitted verdict."""
    out = {}
    for row in rows:
        p = art / "VERDICT" / f"{emit.slugify(row['label'])}.md"
        if not p.is_file():
            bad(f"no verdict for {row['label']}")
            continue
        t = p.read_text(encoding="utf-8")
        permitted = t.startswith("---\nstatus: permitted")
        m = re.search(r"parameter is \*\*(\w+)\*\*", t)
        out[row["label"]] = (permitted, m.group(1) if m else None, t)
    return out


print("\n=== 1. the noise ladder moves the verdict, monotonically ===")

rows = synth.ladder(LEVELS, n_per=N_PER)
with tempfile.TemporaryDirectory() as td:
    art = build(Path(td), rows)
    v = read_verdicts(art, rows)

    # index by (arm, level) using the generating parameters directly
    idx = {}
    for lv in LEVELS:
        for arm in synth.ARMS:
            idx[(arm, lv)] = [r for r in rows
                              if r["truth"] == arm
                              and r["label"].startswith(f"{arm}-{lv:g}-")]

    frac = []
    for lv in LEVELS:
        rs = idx[("good", lv)]
        f = sum(v[r["label"]][0] for r in rs) / len(rs)
        frac.append(f)
    print(f"       permitted fraction, right-model arm: "
          f"{', '.join(f'{lv:g}:{f:.2f}' for lv, f in zip(LEVELS, frac))}")

    check(all(a >= b - 1e-9 for a, b in zip(frac, frac[1:])),
          "permitted fraction never rises as noise rises")
    check(frac[0] >= 0.8,
          f"at {LEVELS[0]:g} noise, {frac[0]*100:.0f}% permitted (>= 80%)")
    check(frac[-1] == 0.0,
          f"at {LEVELS[-1]:g} noise, nothing is permitted")

print("\n=== 2. noisy data is refused as IMPRECISE, not biased ===")

with tempfile.TemporaryDirectory() as td:
    art = build(Path(td), rows)
    v = read_verdicts(art, rows)

    right_refused = [r for r in rows if r["truth"] in RIGHT_MODEL
                     and not v[r["label"]][0]]
    kinds = {v[r["label"]][1] for r in right_refused}
    check(bool(right_refused),
          f"{len(right_refused)} right-model measurements refused at high noise")
    check(kinds == {"imprecise"},
          f"every right-model refusal is 'imprecise' (saw {kinds or 'none'})")

    print("\n=== 3. a wrong model is refused as BIASED, at every noise level ===")
    wrong = [r for r in rows if r["truth"] == "wrongmodel"]
    wrong_perm = [r for r in wrong if v[r["label"]][0]]
    wrong_kinds = {v[r["label"]][1] for r in wrong}
    check(not wrong_perm,
          f"no wrong-model measurement is permitted ({len(wrong)} tested)")
    check(wrong_kinds == {"biased"},
          f"every wrong-model refusal is 'biased' (saw {wrong_kinds})")
    lo = [r for r in idx[("wrongmodel", LEVELS[0])]]
    check(all(v[r["label"]][1] == "biased" for r in lo),
          f"still 'biased' at the lowest noise ({LEVELS[0]:g}) — low noise with "
          f"a poor fit is a wrong model, not bad data")

    print("\n=== 4. an unidentifiable parameter is refused despite a good fit ===")
    trunc = [r for r in rows if r["truth"] == "truncated"]
    check(not any(v[r["label"]][0] for r in trunc),
          f"no truncated-arc measurement is permitted ({len(trunc)} tested)")
    # The point is only about the low-noise end: at high noise a truncated arc
    # also fails the misfit gate, so its refusal would not be evidence that
    # identifiability is doing any work. Restrict to cases that fit WELL.
    clean_trunc = [r for r in trunc if float(r["misfit"]) < synth.MISFIT_MAX]
    worst = max(float(r["misfit"]) for r in clean_trunc)
    check(len(clean_trunc) >= len(trunc) // 2,
          f"{len(clean_trunc)} of {len(trunc)} truncated cases fit better than "
          f"the misfit gate")
    check(all(not v[r["label"]][0] for r in clean_trunc),
          f"...and every one of those is still refused (worst misfit "
          f"{worst*100:.1f}% < {synth.MISFIT_MAX*100:g}% gate) — "
          f"identifiability is not fit quality")

    print("\n=== 5. every refusal says which kind, and never both ===")
    refused = [r for r in rows if not v[r["label"]][0]]
    missing = [r["label"] for r in refused if v[r["label"]][1] is None]
    both = [r["label"] for r in refused
            if "**biased**" in v[r["label"]][2] and
            "**imprecise**" in v[r["label"]][2]]
    check(not missing, f"all {len(refused)} refusals name biased or imprecise")
    check(not both, "no refusal claims both")

    print("\n=== 6. the numbers reach the artifact undistorted ===")
    worst_err = 0.0
    for r in rows:
        t = v[r["label"]][2]
        row_line = next((l for l in t.splitlines()
                         if l.startswith("| misfit ")), "")
        m = re.search(r"\|\s*([\d.]+)%\s*\|", row_line)
        if not m:
            bad(f"no misfit value in verdict for {r['label']}")
            break
        worst_err = max(worst_err, abs(float(m.group(1)) / 100
                                       - float(r["misfit"])))
    check(worst_err <= 5.1e-4,
          f"misfit transcribed within rounding ({worst_err:.2e} worst)")

    print("\n=== 7. gates pass on the tree at every noise level ===")
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "graph_gate.py"),
                         str(art)], capture_output=True, text=True)
    check(rc.returncode == 0,
          "graph_gate PASS — a well-formed tree stays well-formed under noise")

    print("\n=== 8. noise does not propagate into a claim ===")
    noisy_ids = []
    for r in rows:
        if r["truth"] in RIGHT_MODEL and not v[r["label"]][0]:
            noisy_ids.append(
                f"cpt-{synth.SYSTEM}-verdict-{emit.slugify(r['label'])}")
    # The axis is declared honestly: this IS a trend, and along the MEASUREMENT
    # axis, so G9 has no objection. What must stop it is G4 — the verdicts it
    # rests on were refused for noise. Declaring `none` here would have let the
    # check pass for the wrong reason.
    synth.write_finding(art, "noise-claim", "supported", noisy_ids[:6],
                        "R_ct increases with injected noise",
                        axis=f"`injected noise level` in `{synth.DATASET_ID}`")
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "graph_gate.py"),
                         str(art)], capture_output=True, text=True)
    out = rc.stdout + rc.stderr
    check(rc.returncode != 0 and "G4" in out,
          "a finding resting on noise-refused verdicts is FAILED by the gate")


print()
if fails:
    print(f"FAIL — {len(fails)} check(s) failed")
    sys.exit(1)
print("PASS — noisy, mis-modelled and unidentifiable data are each "
      "identified correctly")
