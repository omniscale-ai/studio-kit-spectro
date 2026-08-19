# Provenance for the worked example

The pipeline output the ZnO example artifacts were written from.

These are shipped, rather than referenced, on the kit's own principle: an
artifact that quotes a number ships with the evidence for it. `cfs` is not
needed to check them —

```bash
python3 scripts/check_claims.py
```

re-derives every number quoted in `artifacts/*/examples/` from these tables and
fails on any mismatch.

The examples went stale once before this check existed: tightening the verdict
criteria upstream silently invalidated numbers in a shipped artifact and a
shipped report. The check exists so that cannot recur silently.

| file | what |
|---|---|
| `results_750pass.csv` | 27 spectra, ZnO 750-pass set |
| `results_cseries.csv` | 27 spectra, ZnO C-series (set C) |

Produced by `eis_suite` @ 2026-08-19 (`python run_series.py {750pass,cseries}`).
Columns are the pipeline's own; `scripts/check_claims.py` documents which ones
each claim uses.
