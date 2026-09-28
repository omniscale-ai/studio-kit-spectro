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

  G8  Every FIT has exactly one VERDICT and back, and the tree contains every
      artifact `emitted.json` says was written. Failure prevented: two datasets
      whose measurements are labelled by CONDITION collided on artifact id, so
      the second emit overwrote the first and the tree held 27 spectra where 54
      were expected -- and passed every other gate, because half a run is
      exactly as well-formed as a whole one. G1-G7 ask whether what is present
      is sound; only G8 asks whether it is all there.

      A second instance, found 2026-09-22: the ledger G8 reads was itself
      keyed so that a second emit from one DATASET erased the first, which is
      the normal case when a fit yields more than one parameter. The gate was
      asking a complete question of an incomplete record. See
      `emit_artifacts.write_ledger`.

  G9  A FINDING marked `supported` may not claim a trend along a condition axis
      the DATASET declares SYNTHESIS. Failure prevented: the kit's own flagship
      example -- a rate law fitted across an axis where every value is a
      different sample -- reproduced on a second technique and passing all
      eight of the other gates. G5 made the DATASET *declare* each axis kind;
      nothing made a FINDING *respect* the declaration, so the rule lived in
      FINDING/rules.md, in the template's confound table, and in G4's own
      docstring, and was enforced nowhere.

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
# a Claimed Axis that declares the finding is not a trend across one
NO_AXIS = re.compile(r"^\s*(none|n/?a|not a trend)\b", re.I)


def condition_axes(doc) -> dict:
    """{axis name (lowercased) -> 'MEASUREMENT'|'SYNTHESIS'} for a DATASET.

    The kind is searched for anywhere in the row, like G5 does, so the column
    order of the Condition Axes table is not load-bearing.
    """
    out = {}
    for line in section(doc["text"], "Condition Axes").splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        m = re.search(r"\b(measurement|synthesis)\b", line, re.I)
        if m:
            out[cells[0].lower().strip("* `")] = m.group(1).upper()
    return out


def verdict_permits(doc) -> bool:
    """Does this VERDICT permit the parameter to be used?

    One function, because the question was previously answered in two places
    with the same two regexes composed in opposite orders, and only one order
    was right. `PERMISSIVE` matches the bare word "usable" *inside* the phrase
    "not usable", so `REFUSING and not PERMISSIVE` -- the form G4 used -- is
    False on a refusal whose Call reads "not usable for R_gb". That is the
    phrasing `emit_artifacts.py` writes for 25 of the 54 rows in this kit's own
    provenance tables, so a FINDING marked `status: supported` could rest
    entirely on refusing verdicts and still pass the gate that exists to stop
    exactly that. Found by an independent run of the kit on Zhang et al. 2020
    (Zenodo 3633835), 2026-09-21.

    The frontmatter `status:` is authoritative when present: `emit_artifacts.py`
    already computes it correctly, so re-deriving it by parsing prose is both
    redundant and where the bug lived. Prose is the fallback for hand-written
    verdicts, using the one composition that is correct -- permissive language
    with no refusing language.
    """
    status = (doc.get("fm", {}).get("status") or "").strip().lower()
    if status in ("permitted", "refused"):
        return status == "permitted"
    call = section(doc["text"], "Call")
    return bool(PERMISSIVE.search(call)) and not REFUSING.search(call)


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
LEDGER = "emitted.json"


def gate_completeness(root: Path, index: dict) -> list:
    """G8 -- is the tree ALL there, not merely sound?

    Two independent checks, because they fail apart. Pairing catches a FIT whose
    VERDICT was lost; the ledger catches a whole dataset that was overwritten,
    which pairing cannot see because the survivors are perfectly paired.
    """
    v = []

    def bad(path, msg):
        v.append(dict(gate="G8", path=str(path), message=msg))

    # The kind lives in ONE position of the id, cpt-{system}-{kind}-{slug}.
    # A first version matched the substring "-fit-" anywhere, so a FINDING
    # about a property called R_fit (id ...-finding-trend-cseries-r-fit-...)
    # was taken for a FIT, found to have no VERDICT, and failed the gate 28
    # times over. Found 2026-09-28, the first time machine-emitted findings
    # went through the tree.
    KIND = re.compile(r"^(cpt-[a-z0-9]+-)(fit|verdict)(-[a-z0-9-]+)$")

    def kind_of(i):
        m = KIND.match(i)
        return m.group(2) if m else None

    def swap(i, to):
        return KIND.sub(lambda m: m.group(1) + to + m.group(3), i)

    fits = {i for i in index if kind_of(i) == "fit"}
    verdicts = {i for i in index if kind_of(i) == "verdict"}
    # a VERDICT names its FIT; the id differs only in the kind slug
    for f in sorted(fits):
        if swap(f, "verdict") not in verdicts:
            bad(index[f]["path"], f"{f} has no VERDICT; a parameter without a "
                                  f"verdict is a number nobody can defend")
    for w in sorted(verdicts):
        if swap(w, "fit") not in fits:
            bad(index[w]["path"], f"{w} refers to no FIT in this tree")

    led = root / LEDGER
    if not led.is_file():
        return v
    try:
        doc = json.loads(led.read_text(encoding="utf-8"))
    except ValueError as e:
        bad(led, f"{LEDGER} is not readable JSON: {e}")
        return v

    for dataset, entry in sorted(doc.items()):
        want = set(entry.get("ids") or [])
        missing = sorted(want - set(index))
        if missing:
            n = entry.get("n_measurements", "?")
            bad(led, f"{dataset} emitted {n} measurements "
                     f"({len(want)} artifacts) but {len(missing)} are absent "
                     f"from the tree, e.g. {missing[0]}. An artifact tree that "
                     f"is internally consistent can still be half a run.")
    return v


def gate(docs: dict) -> tuple:
    """Returns (violations, id index)."""
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
            permits = verdict_permits(doc)
            if permits:
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
            if not permits and not BIAS_WORDS.search(call):
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
                refused = [i for i in sorted(vids & set(index))
                           if not verdict_permits(index[i])]
                if refused:
                    bad(doc, "G4", "status: supported, but rests on refusing "
                                   f"verdicts: {', '.join(sorted(refused))}")
            for name, sec in (("Confounds Considered", conf),
                              ("Reproduction", rep)):
                if not sec.strip() or PLACEHOLDER.search(sec):
                    bad(doc, "G4", f"{name} is empty")

            # G9 -- a supported trend may not run along a SYNTHESIS axis
            ax = section(text, "Claimed Axis")
            if not ax.strip() or PLACEHOLDER.search(ax):
                bad(doc, "G9", "Claimed Axis is empty; state the condition "
                               "axis this claim varies along, or 'none' if the "
                               "claim is not a trend across one")
            elif not NO_AXIS.match(ax.strip().lstrip("`*_ ")):
                # Only the FIRST paragraph declares the axis; everything after
                # it is prose that may legitimately quote formulae or statuses
                # in backticks, and an earlier version read those as axis names.
                head = ax.strip().split("\n\n")[0]
                names = re.findall(r"`([^`]+)`", head)
                ds_ids = [n for n in names if "-dataset-" in n]
                axis_names = [n for n in names if "-dataset-" not in n][:1]
                if not ds_ids or not axis_names:
                    bad(doc, "G9", "Claimed Axis must name both the DATASET "
                                   "and the axis in backticks, e.g. "
                                   "`deposition temperature` in "
                                   "`cpt-sys-dataset-run1`")
                else:
                    kinds = {}
                    for d in ds_ids:
                        if d in index:
                            kinds.update(condition_axes(index[d]))
                        else:
                            bad(doc, "G9", f"Claimed Axis cites {d}, which "
                                           f"resolves to no DATASET")
                    for anm in axis_names:
                        kind = kinds.get(anm.lower().strip("* "))
                        if kind is None:
                            bad(doc, "G9", f"Claimed Axis names '{anm}', which "
                                           f"is not a row of that DATASET's "
                                           f"Condition Axes table")
                        elif kind == "SYNTHESIS" and status == "supported":
                            bad(doc, "G9", f"status: supported, but the claim "
                                           f"runs along '{anm}', declared "
                                           f"SYNTHESIS: every value is a "
                                           f"different sample, so this is a "
                                           f"synthesis contrast, not a rate law")

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
    return v, index


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
    violations, index = gate(docs)
    violations += gate_completeness(root, index)

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
