# Markowitz row-count fusion qualification

> REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** Remove one redundant construction scan while preserving retained
capacity, scalar arithmetic, pivot order, live factors and saved copies.
**Architecture:** Initialize `nonzeros=0` and add each row's existing length
while seeding row singletons. No field, cache, buffer, threshold or reset change.
**Spec:** 2026-10-11-simplex-core-architecture-design.md and original S4 scope.

The user resumed original-plan work after the MA detour. S4-AA's observation is
complete and frozen. Its high-water retention is an intentional regrowth contract,
not a leak. The distinct target is the extra `sum(length,rows)` construction pass:
H retained rows are scanned, then n current rows are scanned again for singletons.
After full dictionary reset only rows1:n can contain input entries. Fusing the
count with the singleton pass removes H length queries, including H-n empty tails.
It does not remove the two H-dictionary reset passes or bound retained memory.

## Scope and implementation gate

- [x] Preserve current continuation bytes and fresh refs/full32 groups ANDsessions.
- [x] Prepare a separate whole-source candidate and two renamed private methods
  with an exact inverse. Production source/test/environment remain unchanged.
- [ ] Obtain independent admission for the exact source, test/work/cost driver,
  loader, pins, resource guard, reserved output and fail-closed auditor.
- [ ] Run ONE guarded qualification with the immutable driver below, then verify
  all output/process/source bindings and obtain independent result/work review.
- [ ] Publish a separate closure and exact staged/committed files. Integration
  requires a subsequent concrete permanent-test/source integration subplan;
  qualification alone does not edit production or master.

No full/nested module clone, global method replacement, HH/controller experiment,
old rerun, new LP, tolerance or precision change. The ordinary existing JSimplex
module is loaded from the exact checkout; two new diagnostic private method names
reuse unchanged helpers and types. Source inverse binds all other arithmetic,
reset/ownership/copy/failure branches. Generic dictionary observations are work
instrumentation; arbitrary side-effectful/throwing custom `length` ordering is
not promised. Standard Dict/OrderedDict numerical behavior is the target.

## Concrete numerical scope

One Julia process capped at120 seconds, Julia/BLAS1, heap2GiB, VM8GiB,
availableRAM6GiB, swap1GiB. Existing-only compiled modules, offline/no auto-precompile.
Standing human short-attempt permission applies; no repeated question or long run.

Four work cases: n3/8, retained capacityH=n/64. Counting AbstractDict wrapper
forwards empty/keys/values and data operations. Both constructors receive singular
zero matrices after dirty tail seeding: expected SingularException(1), all rows
cleared/owners retained. Reference row queries [2]*n+[1]*(H-n); candidate [1]*n+
[0]*(H-n). This is a runtime work discriminator, not a production error claim.

24 paired lifecycles: Float32/64, ambient BigFloat and RationalBigInt, Dict and
OrderedDict, three target representations. Initial24 sparse asymmetric tridiagonal
(diagonal5/lower-1/upper2), one saved copy/side, small6/repeatedsmall6/regrown24.
Small uses that sparse formula, dense diagonal n+2/offdiagonal1, or CSC retaining
all explicit zeros of the sparse formula. Compare all numerical factor components,
permutations and scalar values with isequal at all four stages, private workspace
and row-owner identities, retained capacity, inputs and saved factors. Live and
saved F/B solves use known ones, exact Rational or absolute64eps(T) each component.
No full solver or certificate claim; selected factor signature is not whole state.

12 full-refactor cost cases: same four types × n32 sparse, H256→n32 sparse,
and dense32 bypass. Independent side setup and two shape-establishing refactors,
then3warm+7measured alternating pairs,4refactors/window. Every pair compares
factor signatures; terminal F/B checks and input preservation outside timing.
Measure every time/bytes/events/GC and require measured compile/recompile0.
Keep all outliers. Counter traffic/summarysize are not native-free/peak/RSS proof.
Each size/type has one process; inconclusive or adverse costs prohibit a universal
speedup claim and must inform the later integration decision without tuning.

Successful schedule: work8construction attempts; life48constructors48copies,
144refactors480directsolves; cost24constructors48setuprefactors960windowrefactors,
48directsolves. Total source entries80constructors/attempts,1152refactors,
48copies,528directsolves. These are explicit driver entry counts, not complete
PREforward/native/import budgets. Work wrapper creates8workspaces/resets beyond
constructor attempts. Diagnostics include fixed bounded signatures/graph walks,
input copies and known-solution vectors outside timing; GC scheduling neutrality
is not claimed. No new production work, allocation or retained state is introduced.
