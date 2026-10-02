#!/usr/bin/env python3
"""Cross-artifact semantic gate for studio-kit-spectro.

Deterministic checks that exceed what `cfs validate` (static structure) can
express. Each gate exists because a real analysis went wrong in exactly that
way; the docstring for each names the failure it prevents.

  G1  A VERDICT calling a parameter usable must cite evidence for every
      criterion its rules define: the five every model fit has
      (identifiability, misfit, residual structure, noise, instrument range)
      PLUS any the system's ANALYSIS-PLAN declares under `Verdict Criteria`.
      Failure prevented: a fitted curve passing through empty space graded
      "trustworthy" because the summary statistic used was insensitive to the
      failure. The plan-declared part was added 2026-09-30 after a second
      field test (MIS capacitors swept both ways) needed a direction-
      hysteresis criterion and the only place to put it was free text, where
      nothing gated it.

  G2  Every threshold cited in a VERDICT's Evidence must resolve to a
      CALIBRATION artifact. Failure prevented: constants that nobody can say
      where they came from, surviving three revisions of the pipeline.

  G3  A CALIBRATION must state BOTH error rates and the quantity it was scored
      on. Failure prevented: a rule validated on detection rate alone, later
      found to fire on 35% of true negatives; and a constant tuned on one
      quantity while being relied on for another it was blind to.

      Also, since 2026-09-30: a CALIBRATION is valid for the systems its
      `scope:` names (default: its own), and a VERDICT may not cite one
      scoped elsewhere; a CALIBRATION with `basis: inherited` must name the
      calibration it was copied from. Failure prevented: thresholds scored on
      MΩ-scale impedance spectra applied to a kΩ-scale dataset on a different
      instrument, with G3 passing because a scored quantity and two rates
      were *written* -- the gate could not tell "scored here" from "scored
      elsewhere". The second field test had to say so in prose.

  G4  A FINDING may only rest on VERDICTs that permit the parameter it uses,
      and must fill Confounds Considered and Reproduction. Failure prevented:
      an "activation energy" fitted across a synthesis axis, on samples whose
      geometry was never divided out, that reversed sign in the replicate set.

      Also: a FINDING marked `supported` may not rest on a VERDICT whose
      thresholds come from an `inherited` CALIBRATION. Fitting and judging on
      borrowed thresholds is allowed and is marked provisional; claiming on
      them is not. The line is drawn at the claim because that is where a
      borrowed number becomes somebody else's fact.

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

  G10 A DATASET must state its Acquisition Order: the order in which the
      independent variable was traversed, and whether once or both ways.
      Failure prevented: two impedance programmes compared as if alike, one
      swept high→low and the other low→high→low, on films where slow (ionic)
      transport makes the two directions give different spectra -- median 6%
      forward/reverse disagreement in the second set, and nothing in either
      DATASET said which way it had been swept. The same field exists for a
      diffractometer's scan direction, a voltage sweep's hysteresis and a
      temperature ramp; it is a property of the *acquisition*, not of the
      technique, which is why it is a required section and not a note.

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


# Criteria EVERY permitting verdict must speak to, whatever the technique; see
# artifacts/VERDICT/rules.md. This is the floor. A system adds to it by
# declaring criteria in its ANALYSIS-PLAN (`plan_criteria` below); it cannot
# take from it, because these five are properties of fitting a model to data,
# not of impedance.
REQUIRED_EVIDENCE = ["identifiab", "misfit", "residual", "noise", "range"]
BIAS_WORDS = re.compile(r"\b(biased|imprecise)\b", re.I)
# A template placeholder is a short brace token, or a PARAGRAPH that opens
# with a brace -- every template's guidance paragraph does, and a hurried user
# leaves whole paragraphs, not tokens. The first version of this matched a
# brace at the start of any LINE, and a tester's prose that wrapped so a set
# literal "{R_s, absolute R_pol, R_pol fold change}" landed at a line start
# failed the gate (2026-10-01). Guidance always starts a paragraph; wrapped
# prose never does. Checked: 35/35 template sections still caught, 0 false
# positives on the shipped examples.
PLACEHOLDER = re.compile(
    r"\{[a-z_ |/-]+\}|(?:\A|\n[ \t]*\n)[ \t]*\{|TODO|TBD|FIXME", re.I)
ID_SYSTEM = re.compile(r"^cpt-([a-z0-9]+)-")


def system_of(artifact_id: str) -> str:
    m = ID_SYSTEM.match(artifact_id or "")
    return m.group(1) if m else ""


def plan_criteria(index: dict) -> dict:
    """{system: [criterion, ...]} declared under `## Verdict Criteria` in that
    system's ANALYSIS-PLANs.

    Each table row's first cell, or each bullet, is one criterion; it is
    matched against a VERDICT's Evidence the way REQUIRED_EVIDENCE is, as a
    lowercase substring. Plans of any status count, because a declaration can
    only ADD to the floor: a draft plan can make the gate stricter, never
    looser, so there is no bypass in honouring it.
    """
    out: dict = {}
    for i, doc in index.items():
        if doc["kind"] != "ANALYSIS-PLAN":
            continue
        sec = section(doc["text"], "Verdict Criteria")
        if not sec.strip() or PLACEHOLDER.search(sec):
            continue
        for line in sec.splitlines():
            s = line.strip()
            if s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if not cells or set(cells[0]) <= set("-: ") or \
                        cells[0].lower() == "criterion":
                    continue
                name = cells[0]
            elif s[:2] in ("- ", "* "):
                name = s[2:].split("—")[0].split(" - ")[0]
            else:
                continue
            name = name.strip("`* ").lower()
            # a row like "| — | none beyond the floor |" declares nothing
            if re.search(r"[a-z0-9]", name):
                out.setdefault(system_of(i), []).append(name)
    return out


def calib_scope(doc, own_id: str) -> set:
    """Systems a CALIBRATION is declared valid for.

    Frontmatter `scope: zno, ulk` or `scope: any`. Absent means the
    calibration's own system, which is what every calibration written before
    this field existed meant.
    """
    raw = doc["fm"].get("scope", "").strip()
    if not raw:
        return {system_of(own_id)}
    parts = {p.strip().strip("`").lower() for p in raw.split(",")}
    return {p for p in parts if p}


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
    # The `**ID**:` line is the declaration; fall back to the first id of the
    # right kind in the BODY. A first version took the first id of the right
    # kind anywhere in the file, and the moment a CALIBRATION's frontmatter
    # gained `inherited_from: cpt-zno-calib-...` every inherited calibration
    # was identified as its source and 181 verdicts failed G2 (2026-10-02).
    m = re.search(rf"^\*\*ID\*\*:\s*`(cpt-[a-z0-9]+-{kind_slug}-[a-z0-9-]+)`",
                  doc["text"], re.M)
    if m:
        return m.group(1)
    body = re.sub(r"^---\n.*?\n---\n", "", doc["text"], count=1, flags=re.S)
    found = ids_in(body, kind_slug)
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
    declared = plan_criteria(index)
    inherited = {i for i in calib_ids
                 if index[i]["fm"].get("basis", "").strip().lower()
                 == "inherited"}

    def cited_calibs(verdict_doc) -> set:
        return set(ids_in(section(verdict_doc["text"], "Evidence"), "calib"))

    for doc in docs.values():
        kind, text = doc["kind"], doc["text"]
        me = own_id(doc) or ""

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
                extra = [c for c in declared.get(system_of(me), [])
                         if c not in low]
                if extra:
                    bad(doc, "G1", "verdict permits use but Evidence is silent "
                                   f"on a criterion this system's ANALYSIS-PLAN "
                                   f"declares required: {', '.join(extra)}")
            cited = set(ids_in(ev, "calib"))
            if not cited:
                bad(doc, "G2", "Evidence cites no CALIBRATION; every threshold "
                               "must resolve to the ground-truth work that "
                               "licensed it")
            for c in cited - calib_ids:
                bad(doc, "G2", f"Evidence cites {c}, which resolves to no "
                               f"CALIBRATION artifact")
            # G3 (scope) -- a threshold is evidence about the system it was
            # scored on. Citing it from another system is copying a number.
            for c in sorted(cited & calib_ids):
                scope = calib_scope(index[c], c)
                if "any" not in scope and system_of(me) not in scope:
                    bad(doc, "G3", f"cites {c}, scored on system "
                                   f"'{system_of(c)}' and not declared valid "
                                   f"for '{system_of(me)}'. A threshold is "
                                   f"evidence about the data it was scored on; "
                                   f"re-score it here, or write a CALIBRATION "
                                   f"in this system with `basis: inherited` "
                                   f"naming the source, so the borrowing is a "
                                   f"record and not a habit")
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
            basis = doc["fm"].get("basis", "scored").strip().lower()
            if basis not in ("scored", "inherited"):
                bad(doc, "G3", f"basis: {basis!r} is neither 'scored' nor "
                               f"'inherited'")
            elif basis == "inherited":
                # The source is a frontmatter field, not a body mention. A
                # first version accepted any calibration id anywhere in the
                # text, so a calibration that cross-referenced two siblings
                # in ordinary prose passed as "inherited" while naming no
                # source at all (tester, 2026-10-01). Provenance needs a
                # declared position. The source need not resolve in this
                # tree -- it usually lives in another system's project.
                src = ids_in(doc["fm"].get("inherited_from", ""), "calib")
                if not src or me in src:
                    bad(doc, "G3", "basis: inherited, but frontmatter has no "
                                   "`inherited_from:` naming the source "
                                   "CALIBRATION; a cross-reference in the body "
                                   "is not a provenance record")

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
                borrowed = sorted({c for i in vids & set(index)
                                   for c in cited_calibs(index[i]) & inherited})
                if borrowed:
                    bad(doc, "G4", "status: supported, but its verdicts were "
                                   "judged against thresholds inherited from "
                                   "another system, not scored on this one: "
                                   f"{', '.join(borrowed)}. Provisional "
                                   "verdicts may be issued on borrowed "
                                   "thresholds; a claim may not. Re-score, or "
                                   "mark the finding proposed")
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
            # G10 -- how the independent variable was traversed
            acq = section(text, "Acquisition Order")
            if not acq.strip() or PLACEHOLDER.search(acq):
                bad(doc, "G10", "Acquisition Order is empty; state the order "
                                "in which the independent variable was "
                                "traversed and whether once or both ways, or "
                                "'not applicable' with the reason. Two "
                                "datasets swept in opposite directions are "
                                "not comparable until this is known")

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
