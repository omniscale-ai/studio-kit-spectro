#!/usr/bin/env python3
"""Routing tests: does a verdict's call reach the gate meaning the same thing?

Regression home for the G4 bypass found on 2026-09-21 by an independent run of
this kit against Zhang et al. 2020 (Zenodo 3633835). The two scripts classified
verdicts with the same two regexes composed in opposite orders:

    emit_artifacts.py   permitted = PERMISSIVE and not REFUSING      (correct)
    graph_gate.py G4    refused   = REFUSING and not PERMISSIVE      (wrong)

`PERMISSIVE` matched the bare word "usable" inside the phrase "not usable", so
the second form was False on a refusal -- and "not usable for R_gb" is exactly
what emit writes for 25 of the 54 rows in this kit's own provenance tables. A
FINDING marked `status: supported` resting entirely on refused verdicts passed
the gate whose stated purpose is to stop that.

Stdlib only. Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import importlib.util
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


def load(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_kit_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


emit = load("emit_artifacts")
gate = load("graph_gate")


# --------------------------------------------------------------------------
print("\n=== 1. the two scripts classify identically ===")

check(emit.PERMISSIVE.pattern == gate.PERMISSIVE.pattern,
      "PERMISSIVE pattern is identical in both scripts")
check(emit.REFUSING.pattern == gate.REFUSING.pattern,
      "REFUSING pattern is identical in both scripts")

# (call text, may the parameter be used?)
BATTERY = [
    ("R_ct trustworthy", True),
    ("R_gb trustworthy", True),
    ("R_gb is usable, 7.307 MOhm", True),
    ("permitted", True),
    ("usable", True),
    ("not usable for R_ct", False),       # the phrase that broke G4
    ("not usable for R_gb", False),
    ("R_ct refused", False),
    ("R_gb is refused.", False),
    ("R_ct lower bound only", False),
    ("R_gb lower bound only", False),
    ("unusable", False),                  # matched PERMISSIVE before boundaries
    ("Not Usable For R_ct", False),       # case-insensitivity
]

agree = wrong_emit = wrong_gate = 0
for call, expect in BATTERY:
    e = bool(emit.PERMISSIVE.search(call)) and not emit.REFUSING.search(call)
    doc = {"fm": {}, "text": f"## Call\n\n{call}\n"}
    g = gate.verdict_permits(doc)
    if e != g:
        bad(f"scripts disagree on {call!r}: emit={e} gate={g}")
    else:
        agree += 1
    if e != expect:
        wrong_emit += 1
        bad(f"emit misclassifies {call!r}: got {e}, want {expect}")
    if g != expect:
        wrong_gate += 1
        bad(f"gate misclassifies {call!r}: got {g}, want {expect}")

check(agree == len(BATTERY),
      f"all {len(BATTERY)} phrasings classified identically by both scripts")
check(wrong_emit == 0 and wrong_gate == 0,
      f"all {len(BATTERY)} phrasings classified correctly")

# frontmatter is authoritative when present
check(gate.verdict_permits(
    {"fm": {"status": "refused"}, "text": "## Call\n\nR_ct trustworthy\n"}
) is False, "frontmatter status: refused overrides permissive prose")
check(gate.verdict_permits(
    {"fm": {"status": "permitted"}, "text": "## Call\n\nnot usable\n"}
) is True, "frontmatter status: permitted overrides refusing prose")


# --------------------------------------------------------------------------
print("\n=== 2. G4 refuses a finding built on refused verdicts ===")


def build(tmp, rows, calib_flags=(), extra=()):
    art = synth.build_tree(tmp)
    csv_path = synth.write_table(tmp / "results.csv", rows)
    cmd = [sys.executable, str(ROOT / "scripts" / "emit_artifacts.py"),
           str(csv_path), "--system", synth.SYSTEM,
           "--dataset", synth.DATASET_ID, "--scan", synth.SCAN_ID,
           "--out", str(art),
           "--model", "Z(w) = R_s + 1/(1/R_ct + Q (jw)^alpha)",
           "--weighting", "proportional with a 0.2% floor",
           "--weighting-calib", synth.CALIBS["weight"],
           "--misfit-calib", synth.CALIBS["misfit"],
           "--residual-calib", synth.CALIBS["residual"],
           "--params", "R_s,R_ct,alpha",
           "--attest", "tests/test_routing.py",
           *calib_flags, *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        bad(f"emit_artifacts failed: {r.stderr.strip()[:300]}")
    return art


def run_gate(art):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "graph_gate.py"),
                        str(art)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def verdict_ids(art, permitted: bool):
    out = []
    for p in sorted((art / "VERDICT").glob("*.md")):
        if p.name in {"template.md", "rules.md", "checklist.md"}:
            continue
        text = p.read_text(encoding="utf-8")
        is_perm = text.startswith("---\nstatus: permitted")
        if is_perm == permitted:
            m = [l for l in text.splitlines() if l.startswith("**ID**")]
            if m:
                out.append(m[0].split("`")[1])
    return out


# a mixed table: the high-noise rows are refused with the bypass phrase
# ("not usable for R_ct"), the low-noise rows are permitted, so the same
# finding can be tried both ways.
rows = synth.ladder([0.005, 0.30], n_per=4, arms=("good", "noisy"))
with tempfile.TemporaryDirectory() as td:
    art = build(Path(td), rows)
    refused = verdict_ids(art, permitted=False)
    permitted = verdict_ids(art, permitted=True)
    check(len(refused) > 0, f"{len(refused)} refused verdicts produced")

    bypass = [i for i in refused
              if "not usable" in (art / "VERDICT" / f"{i.split('verdict-')[1]}.md"
                                  ).read_text(encoding="utf-8").lower()]
    check(len(bypass) > 0,
          f"{len(bypass)} refusals use the 'not usable' phrasing")

    synth.write_finding(art, "bad", "supported", refused,
                        "R_ct rises with noise level")
    rc, out = run_gate(art)
    check(rc != 0 and "G4" in out,
          "gate FAILS a status:supported finding resting on refused verdicts")

    (art / "FINDING" / "synth-bad.md").unlink()
    if permitted:
        synth.write_finding(art, "good", "supported", permitted,
                            "R_ct is determined in the low-noise arm")
        rc, out = run_gate(art)
        check(rc == 0,
              "gate PASSES the same finding when it rests on permitted verdicts")

    (art / "FINDING").joinpath("synth-good.md").unlink(missing_ok=True)
    synth.write_finding(art, "retracted", "retracted", refused,
                        "R_ct rises with noise level")
    rc, out = run_gate(art)
    check(rc == 0, "gate PASSES a finding on refused verdicts when it is "
                   "marked retracted, not supported")


# --------------------------------------------------------------------------
print("\n=== 3. generated verdicts report their own thresholds faithfully ===")

rows = synth.ladder([0.01], n_per=2, arms=("good",))
with tempfile.TemporaryDirectory() as td:
    art = build(Path(td), rows,
                extra=["--misfit-max", "0.008", "--resid-gate", "0.003",
                       "--noise-max", "0.006"])
    texts = [p.read_text(encoding="utf-8")
             for p in (art / "VERDICT").glob("*.md")
             if p.name not in {"template.md", "rules.md", "checklist.md"}]
    check(bool(texts), "verdicts were written")
    joined = "\n".join(texts)
    check("< 0.8%" in joined, "misfit gate 0.008 renders as 0.8%, not 1%")
    check("0.3%" in joined, "residual gate 0.003 renders as 0.3%, not 0%")
    check("< 0.6%" in joined, "noise gate 0.006 renders as 0.6%, not 1%")
    check("> 0%" not in joined,
          "no threshold renders as '> 0%' (which reads as no threshold)")

# per-criterion calibration ids
with tempfile.TemporaryDirectory() as td:
    art = build(Path(td), rows,
                calib_flags=["--identifiability-calib", synth.CALIBS["window"],
                             "--range-calib", synth.CALIBS["window"],
                             "--noise-calib", synth.CALIBS["noise"]])
    text = next(p.read_text(encoding="utf-8")
                for p in (art / "VERDICT").glob("*.md")
                if p.name not in {"template.md", "rules.md", "checklist.md"})
    ident = next(l for l in text.splitlines() if l.startswith("| identifiability"))
    noise_row = next(l for l in text.splitlines() if l.startswith("| noise"))
    check(synth.CALIBS["window"] in ident,
          "identifiability row cites the calibration that scored it")
    check(synth.CALIBS["noise"] in noise_row,
          "noise row cites the calibration that scored it")
    rc, _ = run_gate(art)
    check(rc == 0, "gate passes with per-criterion calibrations")


print()
if fails:
    print(f"FAIL — {len(fails)} check(s) failed")
    sys.exit(1)
print("PASS — verdict routing is consistent from table to gate")
