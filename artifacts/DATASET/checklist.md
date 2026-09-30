# DATASET — Review Checklist

- [ ] Is every condition axis marked MEASUREMENT or SYNTHESIS?
- [ ] For each SYNTHESIS axis: is it clear that comparisons along it compare
      *different samples*?
- [ ] Is the trusted signal range stated, with the level at both extremes?
- [ ] Is per-sample geometry given, or its absence declared with the list of
      quantities it makes unreportable?
- [ ] Does any geometry parameter correlate with a condition axis? If so, is
      that flagged as a confound for later findings?
- [ ] Is the acquisition order stated — which way, and once or both ways? If
      both ways, is `direction` a MEASUREMENT axis rather than a branch that
      was quietly dropped?
- [ ] Are instrument channels sanity-checked, and sentinel values named?
- [ ] Could someone reproduce the parse from this section alone?
