#!/usr/bin/env bash
# End-to-end test: result table -> FIT + VERDICT artifacts -> gates.
#
# This is the executable form of examples/end-to-end/README.md. It asserts the
# OUTCOME, not just that the commands exit 0 -- a run that produced 27 permitted
# verdicts would "pass" a smoke test while meaning the gates had stopped working.
#
#   tests/run_end_to_end.sh
#
# Exit 0 if the whole chain behaves as documented, 1 otherwise.

set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

PY=${PYTHON:-python3}
fail=0

# checksum the artifacts tree so step 6b can tell "this test changed a file"
# apart from "the file was already modified before the test ran"
tree_sum() { find artifacts -type f -name '*.md' -exec sha256sum {} + | sort | sha256sum; }
BEFORE=$(tree_sum)
step() { printf '\n=== %s ===\n' "$1"; }
ok()   { printf '  ok   %s\n' "$1"; }
bad()  { printf '  FAIL %s\n' "$1"; fail=1; }

step "1. inputs are present"
[ -f tests/provenance/results_750pass.csv ] && ok "provenance table" \
  || bad "provenance table missing"
rows=$($PY -c "import csv;print(sum(1 for r in csv.DictReader(open('tests/provenance/results_750pass.csv')) if r.get('ok')=='True'))")
[ "$rows" = "27" ] && ok "27 usable rows in the table" \
  || bad "expected 27 rows, got $rows"

step "2. emit FIT and VERDICT artifacts"
cp -r artifacts "$OUT/artifacts"
$PY scripts/emit_artifacts.py tests/provenance/results_750pass.csv \
    --system zno --dataset cpt-zno-dataset-750pass \
    --scan cpt-zno-scan-750pass --out "$OUT/artifacts" \
    --model 'Z(w) = R_s + 1/(1/R_gb + Q (jw)^alpha)' \
    --weighting 'sigma_i = sqrt((0.02|Z_i|)^2 + (0.002 p90|Z|)^2)' \
    --weighting-calib cpt-zno-calib-weight-floor \
    --misfit-calib cpt-zno-calib-misfit-metric \
    --residual-calib cpt-zno-calib-residual-structure \
    --attest 'end-to-end test' >/dev/null 2>&1 \
  && ok "emit_artifacts ran" || bad "emit_artifacts failed"

n_fit=$(find "$OUT/artifacts/FIT" -maxdepth 1 -name '*.md' \
        ! -name template.md ! -name rules.md ! -name checklist.md | wc -l)
[ "$n_fit" = "27" ] && ok "27 FIT records" || bad "expected 27 FIT, got $n_fit"

step "3. the outcome is the documented one"
read -r perm refu biased imprec <<<"$($PY - "$OUT" <<'PYEOF'
import pathlib, re, sys
d = pathlib.Path(sys.argv[1]) / "artifacts" / "VERDICT"
skip = {"template.md", "rules.md", "checklist.md"}
perm = refu = biased = imprec = 0
for p in d.glob("*.md"):
    if p.name in skip:
        continue
    s = p.read_text(encoding="utf-8")
    if s.startswith("---\nstatus: permitted"):
        perm += 1
    else:
        refu += 1
        m = re.search(r"parameter is \*\*(\w+)\*\*", s)
        if m and m.group(1) == "biased":
            biased += 1
        elif m and m.group(1) == "imprecise":
            imprec += 1
print(perm, refu, biased, imprec)
PYEOF
)"
[ "$perm" = "17" ] && ok "17 permitted" || bad "expected 17 permitted, got $perm"
[ "$refu" = "10" ] && ok "10 refused"   || bad "expected 10 refused, got $refu"
[ "$biased" = "7" ] && ok "7 refused as biased (wrong model)" \
  || bad "expected 7 biased, got $biased"
[ "$imprec" = "3" ] && ok "3 refused as imprecise (not enough signal)" \
  || bad "expected 3 imprecise, got $imprec"
[ $((biased + imprec)) = "$refu" ] \
  && ok "every refusal says which kind it is" \
  || bad "$((refu - biased - imprec)) refusal(s) do not state biased vs imprecise"

step "4. gates pass on the emitted set"
$PY scripts/graph_gate.py "$OUT/artifacts" >/dev/null 2>&1 \
  && ok "graph_gate PASS" || bad "graph_gate failed on emitted artifacts"

step "5. gates actually bite (negative tests)"
$PY - "$OUT" <<'PYEOF'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]) / "artifacts/CALIBRATION/examples/example-weight-floor.md"
s = p.read_text(encoding="utf-8")
p.write_text(re.sub(r"## Error Rates\n.*?(?=\n## Attestation)",
                    "## Error Rates\n\nThe rule detects the problem reliably.\n",
                    s, flags=re.S), encoding="utf-8")
PYEOF
$PY scripts/graph_gate.py "$OUT/artifacts" >/dev/null 2>&1 \
  && bad "gate did NOT fail on a calibration with no false-positive rate" \
  || ok "gate fails on a calibration with no false-positive rate"

step "6. quoted numbers match provenance"
$PY scripts/check_claims.py >/dev/null 2>&1 \
  && ok "check_claims PASS" || bad "check_claims failed"

# The negative test corrupts a number to prove the check bites -- against the
# SCRATCH COPY, never the working tree. An earlier version edited the real file
# and restored it with `git checkout`, which reverted an uncommitted change and
# shipped the reverted file. A test must not be able to destroy work.
sed -i 's/| misfit | 6\.6% over/| misfit | 9.9% over/' \
  "$OUT/artifacts/VERDICT/examples/example-zno-200c5-dark.md"
if grep -q '9.9% over' "$OUT/artifacts/VERDICT/examples/example-zno-200c5-dark.md"; then
  $PY scripts/check_claims.py --artifacts "$OUT/artifacts" >/dev/null 2>&1 \
    && bad "check_claims did NOT notice a drifted number" \
    || ok "check_claims fails on a drifted number"
else
  bad "negative test edited nothing — it would prove nothing"
fi

step "6b. the test left the working tree untouched"
if [ "$(tree_sum)" = "$BEFORE" ]; then
  ok "no artifact modified by this test"
else
  bad "this test modified the artifacts tree"
fi

step "7. Constructor Studio (optional)"
if command -v cfs >/dev/null 2>&1; then
  tmp=$(mktemp -d)
  ( cd "$tmp" && git init -q . \
    && cfs init --project-name e2e --yes >/dev/null 2>&1 \
    && cfs kit install --path "$ROOT" --install-mode copy >/dev/null 2>&1 ) \
    && ok "cfs kit install" || bad "cfs kit install failed"
  rm -rf "$tmp"
else
  printf '  skip cfs not on PATH (kit still valid; see examples/end-to-end)\n'
fi

printf '\n'
if [ "$fail" = "0" ]; then
  printf 'PASS — the chain behaves as examples/end-to-end/README.md describes\n'
else
  printf 'FAIL\n'
fi
exit $fail
