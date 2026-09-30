#!/usr/bin/env python3
"""The kit applied to a system it was not written for.

Motivated by the second field test (2026-09-28): MIS capacitors on a Zurich
MFIA, kΩ-scale, swept 100 Hz → 5 MHz → 100 Hz, judged with thresholds scored
on MΩ-scale ZnO spectra swept the other way. Everything passed. It should
not have, and the reasons it did are what this file tests:

  1. The verdict's criteria were a fixed five. The one this data needed --
     forward/reverse disagreement -- could only go in free text, where
     nothing required it. Now a system's ANALYSIS-PLAN declares criteria
     under `Verdict Criteria` and G1 requires each of them.

  2. The gate could not tell a calibration scored on this data from one
     copied in: both had a Scored Quantity and two error rates *written*.
     Now a CALIBRATION has a `scope:` and a `basis:`; G3 refuses a verdict
     citing one scoped elsewhere, and G4 refuses a supported FINDING resting
     on an `inherited` one. Provisional verdicts on borrowed thresholds are
     allowed; claims are not.

  3. Nothing in either DATASET said which way it had been swept. G10 makes
     Acquisition Order a required section.

  4. The emitter carried one circuit model's parameter list and its
     identifiability test ("arc closed") as defaults. Now both are declared
     per run; the verdict prints the test it applied.

Stdlib only. Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

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


def ok(m):
    print(f"  ok   {m}")


def bad(m):
    print(f"  FAIL {m}")
    fails.append(m)


def check(c, m):
    ok(m) if c else bad(m)


EMIT = [sys.executable, str(ROOT / "scripts" / "emit_artifacts.py")]
GATE = [sys.executable, str(ROOT / "scripts" / "graph_gate.py")]

BASE = ["--system", synth.SYSTEM, "--dataset", synth.DATASET_ID,
        "--scan", synth.SCAN_ID, "--model", "y = f(x; theta)",
        "--weighting", "proportional",
        "--weighting-calib", synth.CALIBS["weight"],
        "--misfit-calib", synth.CALIBS["misfit"],
        "--residual-calib", synth.CALIBS["residual"],
        "--attest", "tests/test_domain.py"]


def emit(csvp, art, *extra, params="R_s,R_ct,alpha"):
    args = EMIT + [str(csvp), "--out", str(art)] + BASE + list(extra)
    if params:
        args += ["--params", params]
    return subprocess.run(args, capture_output=True, text=True)


def gate(art):
    r = subprocess.run(GATE + [str(art)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def good_tree(td: Path, *extra):
    """A tree of genuinely good measurements, all permitted."""
    art = synth.build_tree(td)
    rows = synth.ladder([0.005], n_per=4, arms=("good",))
    csvp = synth.write_table(td / "results.csv", rows)
    r = emit(csvp, art, *extra)
    if r.returncode != 0:
        bad(f"emit failed: {r.stderr.strip()[:200]}")
    ids = []
    for p in sorted((art / "VERDICT").glob("*.md")):
        t = p.read_text(encoding="utf-8")
        if t.startswith("---\nstatus: permitted"):
            ids.append(next(l for l in t.splitlines()
                            if l.startswith("**ID**")).split("`")[1])
    return art, ids


def set_frontmatter(path: Path, **kv):
    s = path.read_text(encoding="utf-8")
    head, _, rest = s.partition("\n---\n")
    for k, v in kv.items():
        head += f"\n{k}: {v}"
    path.write_text(head + "\n---\n" + rest, encoding="utf-8")


def gate_hits(out, gate_id, needle=""):
    return f"[{gate_id}]" in out and needle.lower() in out.lower()


# --------------------------------------------------------------------------
print("\n=== 0. the synthetic system passes as built ===")
with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    rc, out = gate(art)
    check(rc == 0 and len(ids) == 4, "baseline: 4 permitted verdicts, PASS")
    if rc != 0:
        print("        " + out.strip().splitlines()[-1][:120])

# --------------------------------------------------------------------------
print("\n=== 1. a criterion the plan declares is required by G1 ===")
print("       (the field test's direction-hysteresis case)")
with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    synth.declare_criteria(art, {"direction hysteresis":
                                 "swept both ways; branches must agree"})
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G1", "direction hysteresis"),
          "permitting verdict silent on a declared criterion -> FAIL (G1)")
    n = out.count("[G1]")
    check(n == 4, f"every permitting verdict is caught ({n} of 4)")

with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(
        Path(td), "--extra-criterion",
        f"direction hysteresis|2.1%|< 5%|{synth.CALIBS['misfit']}")
    synth.declare_criteria(art, {"direction hysteresis": "both ways"})
    rc, out = gate(art)
    check(rc == 0, "the same tree with the row emitted -> PASS")

with tempfile.TemporaryDirectory() as td:
    # a refusing verdict need not speak to it: refusals are not claims
    art = synth.build_tree(Path(td))
    rows = synth.ladder([0.5], n_per=3, arms=("noisy",))
    csvp = synth.write_table(Path(td) / "r.csv", rows)
    emit(csvp, art)
    synth.declare_criteria(art, {"direction hysteresis": "both ways"})
    rc, out = gate(art)
    check(rc == 0, "refusing verdicts are not required to speak to it")

with tempfile.TemporaryDirectory() as td:
    # a table row of dashes declares nothing (the ZnO example uses one)
    art, ids = good_tree(Path(td))
    synth.declare_criteria(art, {"—": "none beyond the floor"})
    rc, out = gate(art)
    check(rc == 0, "a '—' placeholder row declares no criterion")

# --------------------------------------------------------------------------
print("\n=== 2. a calibration is evidence about the system it was scored on ===")
with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    cal = art / "CALIBRATION" / "synth-misfit.md"
    set_frontmatter(cal, scope="othersys")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G3", "not declared valid for 'synth'"),
          "verdict citing a calibration scoped to another system -> FAIL (G3)")

with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    set_frontmatter(art / "CALIBRATION" / "synth-misfit.md",
                    scope="othersys, synth")
    rc, out = gate(art)
    check(rc == 0, "scope listing both systems -> PASS")

with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    set_frontmatter(art / "CALIBRATION" / "synth-misfit.md", scope="any")
    rc, out = gate(art)
    check(rc == 0, "scope: any -> PASS")

with tempfile.TemporaryDirectory() as td:
    # the field test's actual shape: a verdict in system B citing system A's
    # calibration directly, id and all
    art, ids = good_tree(Path(td))
    for p in (art / "VERDICT").glob("*.md"):
        s = p.read_text(encoding="utf-8")
        p.write_text(s.replace(synth.CALIBS["misfit"],
                               "cpt-zno-calib-misfit-metric"),
                     encoding="utf-8")
    src = art / "CALIBRATION" / "zno-copied-in.md"
    src.write_text((art / "CALIBRATION" / "synth-misfit.md")
                   .read_text(encoding="utf-8")
                   .replace(synth.CALIBS["misfit"], "cpt-zno-calib-misfit-metric"),
                   encoding="utf-8")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G3", "scored on system 'zno'"),
          "verdicts citing another system's calibration by id -> FAIL (G3)")

# --------------------------------------------------------------------------
print("\n=== 3. borrowing is recorded; it licenses verdicts, not claims ===")
with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    set_frontmatter(art / "CALIBRATION" / "synth-misfit.md", basis="inherited")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G3", "no source"),
          "basis: inherited without naming the source -> FAIL (G3)")

with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    cal = art / "CALIBRATION" / "synth-misfit.md"
    set_frontmatter(cal, basis="inherited")
    cal.write_text(cal.read_text(encoding="utf-8").replace(
        "## Ground Truth\n",
        "## Ground Truth\n\nInherited from `cpt-zno-calib-misfit-metric`, "
        "scored on MΩ-scale ZnO spectra; not re-scored at this scale.\n"),
        encoding="utf-8")
    rc, out = gate(art)
    check(rc == 0, "inherited with the source named, verdicts only -> PASS")

    synth.write_finding(art, "claim", "supported", ids,
                        "R_ct is 0.9 +/- 0.1 across the set", axis="none")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G4", "inherited"),
          "supported FINDING on those verdicts -> FAIL (G4)")

    p = art / "FINDING" / "synth-claim.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "status: supported", "status: proposed", 1), encoding="utf-8")
    rc, out = gate(art)
    check(rc == 0, "the same finding marked proposed -> PASS")

with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    set_frontmatter(art / "CALIBRATION" / "synth-misfit.md", basis="guessed")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G3", "neither"),
          "basis: guessed -> FAIL (G3)")

# --------------------------------------------------------------------------
print("\n=== 4. a DATASET states its acquisition order ===")
with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    ds = art / "DATASET" / "synth-ladder.md"
    s = ds.read_text(encoding="utf-8")
    s = re.sub(r"## Acquisition Order\n.*?(?=\n## )", "", s, flags=re.S)
    ds.write_text(s, encoding="utf-8")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G10", "acquisition order"),
          "DATASET with no Acquisition Order -> FAIL (G10)")

with tempfile.TemporaryDirectory() as td:
    art, ids = good_tree(Path(td))
    ds = art / "DATASET" / "synth-ladder.md"
    s = ds.read_text(encoding="utf-8")
    # the template's own guidance paragraph, left in place unedited
    tmpl = (ROOT / "artifacts" / "DATASET" / "template.md").read_text(encoding="utf-8")
    guidance = re.search(r"## Acquisition Order\n(.*?)(?=\n## )", tmpl, re.S).group(1)
    s = re.sub(r"(## Acquisition Order\n).*?(?=\n## )",
               lambda m: m.group(1) + guidance, s, flags=re.S)
    ds.write_text(s, encoding="utf-8")
    rc, out = gate(art)
    check(rc != 0 and gate_hits(out, "G10"),
          "Acquisition Order left as the template's guidance text -> FAIL (G10)")

# --------------------------------------------------------------------------
print("\n=== 5. the emitter assumes no model ===")
with tempfile.TemporaryDirectory() as td:
    art = synth.build_tree(Path(td))
    rows = synth.ladder([0.005], n_per=1, arms=("good", "truncated"))
    csvp = synth.write_table(Path(td) / "r.csv", rows)
    r = emit(csvp, art, params=None)
    check(r.returncode == 2 and "--params" in r.stderr,
          "--params is required; there is no default parameter list")

    r = emit(csvp, art, "--identifiability-test",
             "peak maximum and both half-maxima inside the scan",
             "--misfit-label", "RMS residual / peak height")
    check(r.returncode == 0, "emit with a declared test and misfit label")
    v_good = (art / "VERDICT" / "good-0-005-00.md").read_text(encoding="utf-8")
    v_trunc = (art / "VERDICT" / "truncated-0-005-00.md").read_text(encoding="utf-8")
    f_good = (art / "FIT" / "good-0-005-00.md").read_text(encoding="utf-8")
    check("test passed: peak maximum and both half-maxima inside the scan"
          in v_good, "the permitted VERDICT prints the test it applied")
    check("test failed: peak maximum and both half-maxima" in v_trunc,
          "the refused VERDICT prints the test that failed")
    check("RMS residual / peak height: **" in f_good,
          "the FIT prints the declared misfit label")
    for name, txt in (("FIT", f_good), ("VERDICT", v_good)):
        check(not re.search(r"\barc\b", txt, re.I),
              f"generated {name} carries no impedance vocabulary of its own")

with tempfile.TemporaryDirectory() as td:
    # an older pipeline still writes `arc_closed`; the table stays readable
    art = synth.build_tree(Path(td))
    rows = synth.ladder([0.005], n_per=1, arms=("good", "truncated"))
    for r_ in rows:
        r_["arc_closed"] = r_.pop("identifiable")
    csvp = Path(td) / "legacy.csv"
    import csv as _csv
    with open(csvp, "w", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    r = emit(csvp, art)
    v_trunc = (art / "VERDICT" / "truncated-0-005-00.md").read_text(encoding="utf-8")
    check(r.returncode == 0 and "test failed" in v_trunc,
          "legacy `arc_closed` column is read as identifiability")

with tempfile.TemporaryDirectory() as td:
    art = synth.build_tree(Path(td))
    rows = synth.ladder([0.005], n_per=1, arms=("good",))
    csvp = synth.write_table(Path(td) / "r.csv", rows)
    r = emit(csvp, art, params="R_s,R_ct,nosuch")
    check(r.returncode == 2 and "nosuch" in r.stderr,
          "a parameter column that does not exist is refused, by name")
    r = emit(csvp, art, "--map", "misfit=chi2")
    check(r.returncode == 2 and "chi2" in r.stderr,
          "a mapped column that does not exist is refused, by name")

print()
if fails:
    print(f"FAIL — {len(fails)} check(s) failed")
    sys.exit(1)
print("PASS — the kit adapts to a system it was not written for, by "
      "declaration rather than by edit")
