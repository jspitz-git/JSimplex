# MA-H: isolated routing candidate preparation

2026-10-14. OFFLINE preparation only. No Julia query/parser/import/compile,
numerical launch or actual src/test/Project/env/CI/master change. The original
MA-F performance rejection remains unchanged; no speedup or production acceptance.

## Candidate and source proof

`results/MA-H/candidate-markowitz.jl` SHA256
`dca3d1c7cabfc6ecf8e09832cadd097bcfe4a6e5982e42d914b72333bf853dea`.
Only the full-forward helper call changes: exact BigFloat or Rational{BigInt}
with positive sparse pivot count uses the existing helper; otherwise the original
inline descending upper loop executes. A false route preserves original arithmetic
order and fresh ordinary division/publication. The preceding lower/dense-core
work and following destination publication are identical.

The complete helper block is byte-identical to MA-E. No ownership, eligibility,
rounding, exception, precision, transpose/copy/refactor or dependency behavior was
changed in the candidate. Exact inverses restore both the MA-E candidate and the
original reference factor source. Indentation is the sole reversible transformation
of the copied inline fallback. Import and Project input copies are unchanged MA-E
texts, and production remains untouched.

Structural RED: four expected missing-route/inverse predicates FALSE, helper
identity TRUE, exit1. Structural GREEN:5/5 PASS. These Python checks establish
source shape/inverses, not Julia syntax or runtime regression sensitivity.
New verification:29/29 PASS,27 read-time hashes, plus19 initial input bindings.
The installed Test/scopedvalues sources are explicitly bound by verification,
not by prepare.py's optional manifest discovery (which added no context pins).
No historical script or audit was imported or executed.

## Prospective tests and costs

Unchanged `candidate-tests.jl` preserves381 existing assertions. New separate
`route-tests.jl` and exact-renamed `reference-forward.jl` add266 assertions across
28 paired full-forward comparisons: child counts126/54/86, combined647 assertions.
See [test contract](results/MA-H/test-contract.md) for source-derived counts and
limits. All new Julia text is UNEXECUTED, including syntax/dispatch/test counts.

Coverage includes Float32/64, Rational{Int} fallback, both target types at zero and
positive sparse pivots, BigFloat128/256/512, scoped/nested rounding, signed zero,
NaN/Inf, rational zero-times-infinity and partial work at bounds exceptions.
Reference/candidate values, sign, precision, retained input/factor values and
unpublished destinations on expected exceptions are compared. Tests use real
backends, shared factor storage with separate copied work, and no global method
replacement. Existing381 retain leaf alias/flags/lifecycle/precision-growth tests.
Value checks do not prove bypass; exact source structure is its separate oracle.

New cold qualification work:28constructors,28backend copies,56full-forward entries
(28exact-reference and28candidate;6expected throwing/50successful). No new refactor,
update or public solver. Owned value/precision/sign snapshots and index copies
outside timed windows add bounded test work at n<=8. They are not observer-neutral
or native-memory-cap evidence. Existing standalone helpers and direct upper/reset
measurements do not exercise the new call-site route.

Candidate hot work adds at most two scalar type-identity tests plus one pivot-count
comparison per full forward solve; non-targets short-circuit the count comparison.
Compiler removal of type checks remains unverified. No additional full-vector scan,
basis solve, copy, conversion, cache or retained field. Nonempty target eligibility
remains O(K), lazy private scratch and ordinary independently owned publication
unchanged. This is a justified narrow routing hypothesis; its net runtime benefit
is unknown. No unnecessary NEW production work or memory has been introduced by
this preparation step, since only isolated candidate/test/documentation files exist.

## Next admission and integrity

[MA-I](../../docs/superpowers/plans/2026-10-14-ma-routing-qualification-admission.md)
freezes a subsequent one-attempt schedule:22serial processes, RED30s,
qualification120s,20cost processes60s each/cost600s/whole750s; existing memory,
thread and process-group/session guards. Original48cases/3warm+7measured pairs,
four repeated calls, all target/control thresholds and all GC/outliers retained.
Cost source ledger is45600selected products/subtractions per full/upper schedule,
91200combined, not91200per schedule. Complete forward gates benefit; unchanged
upper/reset is diagnostic only. Original reference vs this exact candidate only.
No launch without new immutable manifest/controls and independent numerical
admission. Short-run permission already exists; no repeated permission question.

Fresh entry verified refs,90old PGIDs ANDsessions/noJulia, protected user files,
MA-G closure/publication/review and isolated worktree. MA-G current continuation
bindings now map ONLY to MA-H/STATUS.md.before-MA-H and roadmap.md.before-MA-H;
all older mappings remain. Automationpaused/CIoff/HHdisabled. All previous
scripts/raw/reviews/candidates and the MA-H input plan remain frozen.

Independent review is recorded under results/MA-H/review.md/json. Publication
requires its acceptance, a separate PASS closure, exact staged names/blobs and
failfast commit/push with remote verification. The one reference-forward EOF blank
line is preserved from the exact reference function, not normalized away.
