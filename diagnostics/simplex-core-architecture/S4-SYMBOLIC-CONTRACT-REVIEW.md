# S4-E independent numerical/work/memory review

Fresh-context gpt-6-astra/high, read-only, no Julia or audit rerun. Accepted S4-E;
no Critical or Important findings. S4-F suitable after execution clarifications.
Reviewer independently rehashed eight key files (not all542), checked25 gates,
24 comparisons, actual included HH tests and4366 saved assertions. Author's
separate full542 rehash and six supplemental checks passed.

Source tracing confirms input copies, shallow native-copy hazards, numeric
reconstruction, singular mutation-before-throw, private backend discard,
independently extracted HH bases, saved-copy isolation and prepared publication.
Historical wrapper/library limitations, PFI source-only scope and old cost limits
are accurate. No unnecessary production work, allocation or retained memory is
introduced: production/test/CI diff is empty. Future O(n+nnz) pattern guards are
per refactor; CSC copies/numeric/extraction/scaling/adjacency work remains.

Author regraded three Minor plan ambiguities Important because implementation
could otherwise feed sentinel-mutated CSC to a second refactor, omit diagnostic
work from accounting, or misclassify a reference scaling-oracle failure as a
reuse defect. One offline textual RED3missing -> GREEN3/3 fixed the plan: separate
owned side inputs, ten combined extractions/ten graph summaries outside measured
call scopes, and stop/preserve on reference convention mismatch. Original plan
and hashes preserved in results/S4-E/boundary-plan-before-review.md and
plan-amendment.json. No numerical execution/review rerun or weakened oracle.

Final minor (deferred): the source report's history-retirement work wording says
packed entries; implementation loops private update records with length reads
and bounded pool bookkeeping. Retained payload scales with packed entries.
No count oracle or proposed optimization depends on that shorthand; future work
must use the precise distinction. No production issue or rerun is warranted.

Declined claims remain open: true-path numerical qualification, empty/nonfinite
bases, actual borrowed assembly, HH candidate publication/history/prepared/copy
integration, native-memory bounds, asymptotic cost, fullsuite/x64 and old CI cause.
These are not waivers; S4-F is a component gate only. Native HH symbolic reuse
stays disabled. S2-A/S6-J/wholeAF remain rejected; CI remains disabled.
