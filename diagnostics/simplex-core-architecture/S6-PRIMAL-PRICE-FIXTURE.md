# S6-W: deterministic repeated-price budget regression

## Change and evidence

The repeated-price test previously depended on native reconstruction roundoff to
reach price correction. The new scoped Float64 identity-basis fixture seeds the
qualified prices and forwards the real first cost BTRAN before returning the
owned declared vector [1,1,2^-40,0,0,0]. Production code, tolerances, precision,
options and CI configuration are unchanged. All five original assertions and the
publication callback are unchanged. Four added assertions require exactly one
fresh cost BTRAN, one correction BTRAN, two total BTRAN calls and one injection.
Every call is counted after one-shot consumption too; unexpected RHS is rejected.

The native helper and all adjacent testsets remain byte-identical. Scope is the
Float64, non-hypersparse, zero-pivot iteration for four managers. Unused copy,
update and refactor forwarding branches are not general lifecycle qualification.
The constructor owns three length-six vectors and retains no workspace reference.

- `results/S6-W/red-1-*`: unchanged old test, two expected structural failures,
  zero solves, exit1, all 13 audit gates and 617 pins verified. This is a structural
  pre-solve RED, not a fresh numerical failure of the original solver.
- `results/S6-W/green-1-*`: actual changed target 36/36, selected native atomic/
  policy neighbor 68/68 and selected-state preservation 5/5; total109/109, exit0,
  all18 audit gates and617 pins. The diagnostic driver adds only owned before/after
  snapshots around the unchanged iteration call. Permanent tests have no ledger
  or snapshot overhead. These selected snapshots do not establish hidden trajectory
  equivalence or observer neutrality.

The S6-V accepted negative boundary call showed that an extra fresh exact BTRAN
leaves the old event/status oracle true but violates the new budget oracle. That
accepted evidence is reused, not rerun; it is not a mutated-production-loop proof.
All old S6-U/V and full-file/corpus/reference runs are preserved without repetition.
The 77 shared production/runtime/environment/launcher pins match S6-V; see
`results/S6-W/comparability.json`. Test source is intentionally changed.

## Computational and memory review

No production execution frequency or retained memory changes. Cold test setup
creates one six-row fixture per manager, as before; no extra permanent iterations
or solves were added. Per BTRAN, one or two six-element equality scans classify
cost/correction RHS, integer counters are incremented, and the first cost call
copies six declared values after the real solve. Three owned length-six vectors
are retained by the wrapper, without diagnostic call/event histories. No benchmark
or speedup claim is warranted. Fresh independent gpt-6-astra review found no findings or unnecessary production
work/memory. Actual-master gate passed41/41 (36target+5selected-state),19audit
gates617pins,exit0. Test-only4c42fe3 -> masterb9e7cb1; exact GREEN/master test
source and user hashes verified. See S6-PRIMAL-PRICE-FIXTURE-REVIEW.md.

## Limitations

This is a deterministic regression for the one-attempt budget, not an explanation
of the historical x64 backend path. Native integration coverage is retained.
Full-suite/x64 success and broader S6 remain open. No safeguard/assertion weakening.
