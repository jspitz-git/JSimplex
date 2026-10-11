# S3-B freshly canonical output support

Status: reviewed, integration-tested1611/1611 and pushed. Productionb6a4064 -> masterb720674.

## Contract and computational work

Only the immediately completed indexed/empty producer grants the local canonical
fact. The output-support consumer then reads the owned index count without a
second compaction. The generic four-argument helper remains conservative because
valid support may contain canceled entries. Dense fallback rebuilds and external
finite/count checks remain; the actual post-fallback mode decides eligibility.
No public option, numerical tolerance, coefficient pruning or arithmetic changed.

The affected frequency is each successful pipeline FTRAN/BTRAN/pricing operation
(and their weight/BFRT consumers). Removed work is one bounded owner lookup and
one O(s) scan of output support. Producer compaction and ordinary input compaction
remain. No added basis solve, matrix/vector scan, copy, conversion, retained array
or workspace field. Empty producers save a zero-length compaction call. Dense
and external bodies remain unchanged apart from a local Boolean branch.

The exact producer proof and failure/alias boundaries are in the
[pipeline canonical-support subplan](../../docs/superpowers/plans/2026-10-11-pipeline-canonical-support.md).
A valid cache alone never establishes this stronger contract. Failed producers
still invalidate support; callbacks cannot run between successful producer return
and immediate support consumption. HH basis fallback keeps dense reconstruction.

## Accepted correctness and work evidence

- Unchanged-production census:20000 assertions,1900 cases across5precisions,
  5managers,2backends,0/1 actual updates,empty/sparse/dense input,forced modes,
  both solve directions,pricing and external destinations.
- Work RED:74pass/6intended failures,0errors; identical small GREEN80/80.
- Permanent tests:1611/1611. Extended GREEN20000/20000,1900 paired cases.
  Modes,support cardinalities,rebuilds and rebuild scan lengths match exactly.
  Each run asserts values against explicit basis equations/pricing products;
  this matrix did not serialize per-case value hashes.
- Paired work audit removes exactly992 output-consumer compactions and5156
  visited entries.600 empty producers contribute calls but no visited entries.
  Input compaction, dense rebuild and external check counts are unchanged.
- Existing focused regressions:10645pass/0fail/1driver missing-fixture error,
  including the full pipeline solver groups and480 HH supplementary assertions.
  Targeted follow-up closes the affected pricing alias/storage testset:9/9.
  Broad passed groups were not repeated for that harness error.

All above completed attempts recorded unchanged pins. Final process reports were
read before separate host checks confirmed runner, child and driver absence.
Normal compilation was used. Full project suite is not claimed; earlier baseline
compilation stalls and incomplete broader S6 coverage remain in STATUS.

## Cost evidence and preserved fixture limitation

Cost-1 failed before measurement because the diagnostic AST rename did not unwrap
pricing's return annotation. Cost-2 fixed that diagnostic and completed828samples,
276warmups,23fixtures before Float32/Markowitz PFI dense/history8 initialization
failed at pivot3 with NUMERICAL_ERROR (primal point could not be certified).
Targeted fixture-probe-1 reproduced identical returned status, iteration/update
counts and infeasibilities in old/new code for PFI and HH. This is preserved
preexisting fixture failure, not successful construction or an accepted solve.
No tolerances, coefficients or arithmetic were changed. Dense/history8 Float64
coverage includes all5managers; Float32 dense/history8 timing is missing.

Targeted remaining run completed3 HH/Float32 fixtures,108samples/36warmups,exit0.
The audit explicitly combines completed groups of the preserved exit1 attempt
with the exit0 follow-up:936samples,312warmups,26of28fixtures,156groups. Every
group has3interleaved pairs,exact output hashes,identical actual modes,zero measured
compilation and equal allocation bytes/events. Setup and warmup are separate.
Independent residual/pricing and canonical-support checks occur outside timing.
The old helper is an exact renamed source extraction; cloned current pipeline
bodies differ only in calling that helper without the new canonical argument.

For64 actual-sparse groups, median of group candidate/control median ratios is
0.9367; group range0.7951–1.0643. For92 actual-dense groups it is1.0020, range
0.5946–1.2329. Individual paired ratios range0.2922–2.9003(sparse) and
0.2518–3.0361(dense). These tiny batches are noisy; no universal elapsed speedup
or proof of regression-free individual timing follows. The exact work savings,
unchanged arithmetic, zero new storage and equal allocation counts are stronger
local evidence than the elapsed estimate. Raw measurements and every group are
in results/S3-B/support-cost-audit.json and companion TOML files.

Both actual code paths retain their pipeline clock/cost updates, while fixed outer
modes prevent cost-driven selection from changing the comparison. Existing
optional automatic selection may react to changed timings. Controlled legacy
hypersparse=false is unchanged; no whole-medium or automatic-policy trajectory
claim is made. The additional80paired Float64 solver state/event cases passed1041assertions: both algorithms,all5managers,2backends,sparse/dense fixtures and forcedsparse/dense. Entry/final state hashes,completion states,event order/counts,iterations,refactorizations and kernel counts match exactly. Exit0/pins unchanged; separate host runner/child/driver absence confirmed.

## Review and integration

Fresh independent reviewer (gpt-6-astra, read-only, no Julia) approves the narrow
change, with no critical, important or minor finding requiring a fix. Source proof
covers both actual-mode call sites, all producer exits, finite dense reload,
alias checks and exceptional invalidation. Reviewer independently reproduced the
1900work pairs,936cost records/156groups,80trajectory pairs,current source hashes
and exact renamed baseline helper.

Explicit AGENTS judgment: no unnecessary added work, allocations or retention.
Each eligible successful owned sparse/empty call replaces one lookup through six
owners and one O(s) compaction by constant selection and length access. No new
solve/copy/conversion/matrix traversal or persistent metadata. Existing producer
cost and all necessary independent numerical protections remain.

Reviewer declined broader claims, and the author accepts these scope rulings:
no universal elapsed speedup or automatic-policy trajectory guarantee; no timing
claim for the two failed Float32 dense/history8 fixtures; full project suite and
long/external S6 runs remain incomplete. Unrelated S1/S2/S4/S5 work was not part of
this local diff. These limits are preserved rather than silently treated as passed.
No deferred minor issue. Review inspected saved numerical logs; no duplicate
numerical execution was launched by the reviewer.

Productionb6a40649f5f04b6c20328dc55ef41b75462a78c9 was cherry-picked to
masterb720674097f662e2f8c3ea81590ea551d66a7e9a. The three integrated source/test files
match the qualified candidate exactly, main user-file/environment hashes match,
and master permanent regression passed1611/1611,exit0/pins unchanged. Runner289833/
child289858/driver absence was separately verified before the authorized push.
Remote masterb720674 was read back with git ls-remote. Diagnostics and rejected prototypes remain on the architecture branch.
