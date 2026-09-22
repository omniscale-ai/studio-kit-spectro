#!/usr/bin/env python3
"""G8 completeness: does the ledger survive more than one emit per DATASET?

Regression home for the defect found by the Pd-Si XRD field test (Zenodo
20798555, 2026-09-22). `write_ledger()` did:

    doc[a.dataset] = dict(..., ids=sorted(emitted))

which discarded every earlier emit's ids for that DATASET. Not an exotic case:
one fit commonly yields several parameters, FIT and VERDICT pair one-to-one, so
each parameter needs its own emit -- and the second erased the first. The field
test then deleted all 150 artifacts of its PRIMARY parameter and watched
graph_gate report PASS.

That is the silent loss G8 exists to catch, occurring inside G8's own input.
G1-G7 ask whether what is present is sound; G8 asks whether it is all there,
and it was asking against a record that had forgotten half the run.

Stdlib only. Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import json
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


def emit(art: Path, csv_path: Path, extra=()):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "emit_artifacts.py"),
         str(csv_path), "--system", synth.SYSTEM,
         "--dataset", synth.DATASET_ID, "--scan", synth.SCAN_ID,
         "--out", str(art), "--model", "Z = R_s + arc",
         "--weighting", "proportional",
         "--weighting-calib", synth.CALIBS["weight"],
         "--misfit-calib", synth.CALIBS["misfit"],
         "--residual-calib", synth.CALIBS["residual"],
         "--params", "R_s,R_ct,alpha", "--attest", "tests/test_completeness.py",
         *extra], capture_output=True, text=True)


def gate(art: Path):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "graph_gate.py"),
                        str(art)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def param_rows(prefix, n=5):
    rows = synth.ladder([0.01], n_per=n, arms=("good",))
    for r in rows:
        r["label"] = f"{prefix}-{r['label']}"
    return rows


print("\n=== 1. two parameters from one DATASET both reach the ledger ===")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    art = synth.build_tree(td)
    a = synth.write_table(td / "size.csv", param_rows("size"))
    b = synth.write_table(td / "position.csv", param_rows("position"))
    check(emit(art, a).returncode == 0, "emit 1 (size) ran")
    check(emit(art, b).returncode == 0, "emit 2 (position) ran")

    led = json.loads((art / "emitted.json").read_text())
    entry = led[synth.DATASET_ID]
    ids = entry["ids"]
    n_size = sum(1 for i in ids if "-size-" in i)
    n_pos = sum(1 for i in ids if "-position-" in i)
    check(n_size > 0 and n_pos > 0,
          f"ledger records BOTH emits ({n_size} size ids, {n_pos} position ids)")
    check(len(entry.get("emits") or {}) == 2,
          "ledger keeps a per-source breakdown of the two emits")
    check(entry["n_measurements"] == 10,
          f"n_measurements is the total over sources "
          f"(got {entry['n_measurements']}, want 10)")

    rc, _ = gate(art)
    check(rc == 0, "gate passes on the complete tree")

    # THE test: delete the first parameter's artifacts entirely
    n = 0
    for kind in ("FIT", "VERDICT"):
        for p in (art / kind).glob("size-*.md"):
            p.unlink()
            n += 1
    rc, out = gate(art)
    check(rc != 0 and "G8" in out,
          f"deleting all {n} artifacts of the FIRST parameter now FAILS G8")


print("\n=== 2. re-emitting the same source is idempotent ===")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    art = synth.build_tree(td)
    a = synth.write_table(td / "size.csv", param_rows("size"))
    emit(art, a)
    first = json.loads((art / "emitted.json").read_text())[synth.DATASET_ID]
    emit(art, a)
    second = json.loads((art / "emitted.json").read_text())[synth.DATASET_ID]
    check(first["ids"] == second["ids"],
          "a re-run of the same table leaves the id list unchanged")
    check(first["n_measurements"] == second["n_measurements"] == 5,
          f"n_measurements does not double on a re-run "
          f"({first['n_measurements']} -> {second['n_measurements']})")


print("\n=== 3. a ledger written by the pre-fix version still works ===")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    art = synth.build_tree(td)
    a = synth.write_table(td / "size.csv", param_rows("size"))
    emit(art, a)
    # rewrite the ledger in the OLD shape: no `emits`, a single `source`
    led = json.loads((art / "emitted.json").read_text())
    e = led[synth.DATASET_ID]
    led[synth.DATASET_ID] = dict(source=str(a), system=synth.SYSTEM,
                                 scan=synth.SCAN_ID, date="2026-09-01",
                                 n_measurements=5, attest="old version",
                                 ids=e["ids"])
    (art / "emitted.json").write_text(json.dumps(led, indent=1))

    b = synth.write_table(td / "position.csv", param_rows("position"))
    emit(art, b)
    entry = json.loads((art / "emitted.json").read_text())[synth.DATASET_ID]
    ids = entry["ids"]
    check(sum(1 for i in ids if "-size-" in i) > 0,
          "ids from the OLD-format entry are migrated, not dropped")
    check(sum(1 for i in ids if "-position-" in i) > 0,
          "ids from the new emit are present too")
    rc, _ = gate(art)
    check(rc == 0, "gate passes on the migrated tree")


print()
if fails:
    print(f"FAIL — {len(fails)} check(s) failed")
    sys.exit(1)
print("PASS — the ledger records every emit, so G8 can see the whole run")
