#!/usr/bin/env bash
# The whole test suite.
#
#   tests/run_all.sh
#
# Three layers, in increasing order of what they can catch:
#
#   run_end_to_end.sh  replays one REAL dataset and asserts the documented
#                      outcome (17 permitted / 10 refused, split 7 biased and
#                      3 imprecise). Catches "the chain stopped working".
#
#   test_routing.py    checks that a verdict means the same thing to
#                      emit_artifacts.py and to graph_gate.py. Regression home
#                      for the G4 bypass, where the two scripts composed the
#                      same regexes in opposite orders and a finding built on
#                      refused verdicts passed the gate meant to stop it.
#
#   test_domain.py     the kit applied to a system it was not written for:
#                      a plan-declared verdict criterion is required (G1), a
#                      calibration from another system is refused (G3), a
#                      borrowed one licenses verdicts but no supported
#                      finding (G4), a DATASET must state its acquisition
#                      order (G10), and the emitter carries no model of its
#                      own (identifiability test and parameter list are
#                      declared, not defaulted).
#
#   test_noise.py      feeds SYNTHETIC data whose truth is known by
#                      construction and checks the routing: noisy -> imprecise,
#                      mis-modelled -> biased, unidentifiable -> refused even
#                      when the fit is excellent, and none of them reaching a
#                      supported finding. The real dataset cannot test this,
#                      because it carries no labels.
#
# Stdlib Python only, no network. Exit 0 if everything passes.

set -uo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
fail=0

# the suite must not modify the shipped artifacts; compare to the pre-test
# state rather than to HEAD, so an unrelated uncommitted edit is not misreported
tree_sum() { find artifacts -type f -name '*.md' -exec sha256sum {} + | sort | sha256sum; }
BEFORE=$(tree_sum)

hr() { printf '\n\033[1m──────── %s ────────\033[0m\n' "$1"; }

hr "1/7  end-to-end on real data"
if bash tests/run_end_to_end.sh; then :; else fail=1; fi

hr "2/7  verdict routing, output format, extra criteria"
if $PY tests/test_routing.py; then :; else fail=1; fi

hr "3/7  noise, bias and identifiability"
if $PY tests/test_noise.py; then :; else fail=1; fi

hr "4/7  completeness: the ledger sees every emit (G8)"
if $PY tests/test_completeness.py; then :; else fail=1; fi

hr "5/7  axis kind: no supported trend along a synthesis axis (G9)"
if $PY tests/test_axis_kind.py; then :; else fail=1; fi

hr "6/7  domain adaptation: declared criteria, calibration scope, acquisition order (G1/G3/G4/G10)"
if $PY tests/test_domain.py; then :; else fail=1; fi

hr "7/7  the suite left the working tree untouched"
if [ "$(tree_sum)" = "$BEFORE" ]; then
  printf '  ok   no shipped artifact was modified\n'
else
  printf '  FAIL the suite modified artifacts/ — tests must work on copies\n'
  fail=1
fi

echo
if [ "$fail" = 0 ]; then
  echo "ALL PASS"
else
  echo "FAILURES — see above"
fi
exit $fail
