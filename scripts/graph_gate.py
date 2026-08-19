#!/usr/bin/env python3
"""Cross-artifact semantic gate for studio-kit-spectro.

Deterministic checks that exceed what `cfs validate` (static structure) can
express. Each gate exists because a real analysis went wrong in exactly that
way; the docstring for each names the failure it prevents.

  G1  A VERDICT calling a parameter usable must cite evidence for every
      criterion its rules define. Failure prevented: a fitted curve passing
      through empty space graded "trustworthy" because the summary statistic
      used was insensitive to the failure.

  G2  Every threshold cited in a VERDICT's Evidence must resolve to a
      CALIBRATION artifact. Failure prevented: constants that nobody can say
      where they came from, surviving three revisions of the pipeline.

  G3  A CALIBRATION must state BOTH error rates and the quantity it was scored
      on. Failure prevented: a rule validated on detection rate alone, later
      found to fire on 35% of true negatives; and a constant tuned on one
      quantity while being relied on for another it was blind to.

  G4  A FINDING may only rest on VERDICTs that permit the parameter it uses,
      and must fill Confounds Considered and Reproduction. Failure prevented:
      an "activation energy" fitted across a synthesis axis, on samples whose
      geometry was never divided out, that reversed sign in the replicate set.

  G5  A DATASET must declare every condition axis as MEASUREMENT or SYNTHESIS.
      Failure prevented: the same, one step earlier.

  G6  ANALYSIS-PLAN status `approved` requires a filled Approval section.

  G7  Script-generated kinds (ARTEFACT-SCAN, FIT, VERDICT, CALIBRATION) must
      carry an Attestation naming the script. Failure prevented: hand-written
      records of automated steps.

Usage:  python3 graph_gate.py <artifacts-root> [--json]
Exit:   0 all gates pass, 1 violations found, 2 usage/parse error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KINDS = ["DATASET", "ARTEFACT-SCAN", "FIT", "VERDICT", "CALIBRATION",
         "FINDING", "ANALYSIS-PLAN"]
GENERATED = ["ARTEFACT-SCAN", "FIT", "VERDICT", "CALIBRATION"]
SKIP = {"template.md", "rules.md", "checklist.md"}

# a verdict that permits use of a parameter
PERMISSIVE = re.compile(r"\b(usable|trustworthy|permitted)\b", re.I)
REFUSING = re.compile(r"\b(not usable|refused|unusable|lower bound)\b", re.I)
# criteria a verdict must speak to; see artifacts/VERDICT/rules.md
REQUIRED_EVIDENCE = ["identifiab", "misfit", "residual", "noise", "range"]
BIAS_WORDS = re.compile(r"\b(biased|imprecise)\b", re.I)
PLACEHOLDER = re.compile(r"\{[a-z_ |/-]+\}|TODO|TBD|FIXME", re.I)


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()
    return fm


def section(text: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\s*\n(.*?)(?=^##\s|\Z)",
                  text, re.DOTALL | re.MULTILINE)
    return m.group(1) if m else ""


def ids_in(text: str, kind: str) -> list:
    return re.findall(rf"cpt-[a-z0-9]+-{kind}-[a-z0-9-]+", text)


def collect(root: Path) -> dict:
    docs = {}
    for kind in KINDS:
        d = root / kind
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.md")):
            if p.name in SKIP:
                continue
            text = p.read_text(encoding="utf-8")
            docs[p] = dict(kind=kind, text=text, fm=frontmatter(text),
                           path=p)
    return docs


def own_id(doc) -> str | None:
    kind_slug = {"DATASET": "dataset", "ARTEFACT-SCAN": "scan", "FIT": "fit",
                 "VERDICT": "verdict", "CALIBRATION": "calib",
                 "FINDING": "finding", "ANALYSIS-PLAN": "aplan"}[doc["kind"]]
    found = ids_in(doc["text"], kind_slug)
    return found[0] if found else None


# --------------------------------------------------------------------------
def gate(docs: dict) -> list:
    """Returns a list of violation dicts."""
    v = []

    def bad(doc, gate_id, msg):
        v.append(dict(gate=gate_id, path=str(doc["path"]), message=msg))

    index = {}
    for doc in docs.values():
        i = own_id(doc)
        if i:
            index[i] = doc

    calib_ids = {i for i in index if "-calib-" in i}

    for doc in docs.values():
        kind, text = doc["kind"], doc["text"]

        # G7 -- generated kinds must be attested
        if kind in GENERATED:
            att = section(text, "Attestation")
            if not att.strip() or PLACEHOLDER.search(att):
                bad(doc, "G7", f"{kind} has no filled Attestation section; "
                               f"records of automated steps must name the "
                               f"script that produced them")

        # G1/G2 -- verdict evidence
        if kind == "VERDICT":
            ev = section(text, "Evidence")
            call = section(text, "Call")
            low = ev.lower()
            if PERMISSIVE.search(call) and not REFUSING.search(call):
                missing = [c for c in REQUIRED_EVIDENCE if c not in low]
                if missing:
                    bad(doc, "G1", "verdict permits use but Evidence is silent "
                                   f"on: {', '.join(missing)}")
            cited = set(ids_in(ev, "calib"))
            if not cited:
                bad(doc, "G2", "Evidence cites no CALIBRATION; every threshold "
                               "must resolve to the ground-truth work that "
                               "licensed it")
            for c in cited - calib_ids:
                bad(doc, "G2", f"Evidence cites {c}, which resolves to no "
                               f"CALIBRATION artifact")
            if REFUSING.search(call) and not BIAS_WORDS.search(call):
                bad(doc, "G1", "verdict refuses a parameter without saying "
                               "whether it is biased (wrong model) or "
                               "imprecise (noise); these demand opposite "
                               "responses")

        # G3 -- calibrations must be honest about what they measured
        if kind == "CALIBRATION":
            scored = section(text, "Scored Quantity")
            errs = section(text, "Error Rates")
            if not scored.strip() or PLACEHOLDER.search(scored):
                bad(doc, "G3", "Scored Quantity is empty; a constant scored on "
                               "the wrong quantity is the commonest quiet "
                               "failure")
            if not errs.strip() or PLACEHOLDER.search(errs):
                bad(doc, "G3", "Error Rates is empty")
            elif not re.search(r"false[ -]positive", errs, re.I):
                bad(doc, "G3", "Error Rates states no false-positive rate; "
                               "detection alone is not a calibration, since a "
                               "rule that fires on everything detects "
                               "everything")

        # G4 -- findings rest on permitting verdicts
        if kind == "FINDING":
            sup = section(text, "Supporting Verdicts")
            conf = section(text, "Confounds Considered")
            rep = section(text, "Reproduction")
            vids = set(ids_in(sup, "verdict"))
            if not vids:
                bad(doc, "G4", "Supporting Verdicts cites no VERDICT")
            unresolved = vids - set(index)
            for u in unresolved:
                bad(doc, "G4", f"cites {u}, which resolves to no VERDICT")
            status = doc["fm"].get("status", "").lower()
            if status == "supported":
                refused = [i for i in vids & set(index)
                           if REFUSING.search(section(index[i]["text"], "Call"))
                           and not PERMISSIVE.search(
                               section(index[i]["text"], "Call"))]
                if refused:
                    bad(doc, "G4", "status: supported, but rests on refusing "
                                   f"verdicts: {', '.join(sorted(refused))}")
            for name, sec in (("Confounds Considered", conf),
                              ("Reproduction", rep)):
                if not sec.strip() or PLACEHOLDER.search(sec):
                    bad(doc, "G4", f"{name} is empty")

        # G5 -- condition axes declared
        if kind == "DATASET":
            cond = section(text, "Condition Axes")
            if not cond.strip() or PLACEHOLDER.search(cond):
                bad(doc, "G5", "Condition Axes is empty")
            else:
                rows = [l for l in cond.splitlines()
                        if l.strip().startswith("|") and "---" not in l]
                body = rows[1:] if len(rows) > 1 else []
                for r in body:
                    if not re.search(r"\b(measurement|synthesis)\b", r, re.I):
                        bad(doc, "G5", "condition axis row declares neither "
                                       f"MEASUREMENT nor SYNTHESIS: "
                                       f"{r.strip()[:70]}")

        # G6 -- plan approval
        if kind == "ANALYSIS-PLAN" and doc["fm"].get("status") == "approved":
            ap = section(text, "Approval")
            if not ap.strip() or PLACEHOLDER.search(ap):
                bad(doc, "G6", "status: approved with an empty Approval "
                               "section")
    return v


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if len(args) != 1:
        print(__doc__)
        return 2
    root = Path(args[0])
    if not root.is_dir():
        print(f"graph_gate: {root} is not a directory")
        return 2

    docs = collect(root)
    violations = gate(docs)

    if as_json:
        print(json.dumps(dict(scanned=len(docs), violations=violations),
                         indent=2))
    else:
        print(f"graph_gate: {len(docs)} artifacts scanned")
        by_kind = {}
        for d in docs.values():
            by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
        for k in KINDS:
            if by_kind.get(k):
                print(f"  {k:<15s} {by_kind[k]}")
        if violations:
            print()
            for x in violations:
                print(f"  [{x['gate']}] {x['path']}\n        {x['message']}")
            print(f"\nFAIL — {len(violations)} violation(s)")
        else:
            print("\nPASS")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
