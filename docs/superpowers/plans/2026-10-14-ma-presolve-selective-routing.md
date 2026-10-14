# MA-K: Selective Rational Presolver MA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Qualify selective MA additions in eight-term general rational equality
bound checks while refusing a candidate that slows the short/simple controls.

**Architecture:** Keep the generic function intact. Add a narrowly typed route
with an early, in-loop one-shot selection and private scratch only after that
selection succeeds. Separate offline preparation, bounded component qualification,
and any later production integration.

**Tech Stack:** Julia1.13, installed MutableArithmetics, Rational{BigInt}, Test,
Python3 for offline exact oracles and fail-closed launch/audit artifacts.

**Spec:** [MA-K design](../specs/2026-10-14-ma-presolve-selective-routing-design.md).

## Global Constraints

- Planning/review only in MA-K. No Julia/query/parser/import/compile, candidate,
  launcher, production/test/environment/CI change in this step.
- Only exact Rational{BigInt} model + ordinary typed Vector row + length8 may
  activate. Aggregation's2–8 row cap, fill<=10 and total update<=200000 stay fixed.
- No pre-scan, eligibility cache, new traversal, coefficient omission, changed
  products/order/final predicates, tolerance/precision changes or safeguards.
- Every MA destination and buffer has private mutable leaves; no scratch escapes.
- Freeze old evidence. MA-I and unconditional MA-J remain unpromoted. No old
  driver/auditor reruns or HH/DSE/import/isolation/cleanup-omission reopening.
- Automation paused, CI off, HH reuse disabled; preserve user files and master.
- Before future numerical work or pinned continuation edits: fresh refs, boot,
  start_ticks/command and complete previous PGIDs AND sessions/noJulia. Preserve
  exact before texts and explicit historical hash mappings.
- Future numerics: one Julia at a time, Julia/BLAS1, heap2GiB, VM8GiB, available
  RAM>=6GiB, swap<=1GiB. No hours-long/full-suite/excluded-model runs.

## Review Focus

1. Short rows and simple eight-term rows: no scratch, unchanged result/inputs,
   and measured dispatch/classifier overhead must pass Task2 control gates.
2. Shared numerator/denominator owners, shared prefix then divergence and zero
   sums: Task1 ownership tests and Task2 exact/input checks must reject corruption.
3. Infinite bounds, zero/unit coefficients, all pivot positions/signs and tight
   equality boundaries: preserve early exits and Boolean decisions (Task1 grid).
4. Other scalar/container types and BigFloat stored/ambient precision mismatch:
   generic fallback and precision restoration remain exact (Task1 fallback tests).
5. Expensive prefix followed by cheap/cancelled/unbounded tail, or late general
   work: Task1 route assertions and Task2 controls expose false-positive setup cost.

---

## File map and source basis

Current source: `src/presolve_aggregation.jl` (`_equality_implies_column_bounds`
lines233–333 and `aggregate_sparse_equalities`); `src/presolve_rows.jl`
(`_row_entries` returns Vector{Vector{Tuple{Int,T}}}); `src/model.jl` for model
ownership. Read exact current definitions before preparing, not stale line numbers.
MA-J source reference/private_add and accepted raw are evidence only.

MA-L creates `diagnostics/simplex-core-architecture/results/MA-L/` with
`reference.jl`, `candidate.jl`, `tests.jl`, `fixtures.json`, `inverse.json`,
`source-check.py`, `source-check.json`, `review.md`, `review.json`.
MA-M later creates a separate directory with its own `admission.md`, `driver.jl`,
`launcher.py`, `audit.py`, `required-paths.json`, `pins.json`, review and distinct
`run-1/`, `run-2/`, `run-3/` outputs. No file is reused as a mutable old artifact.
Production files and dependencies remain untouched through component acceptance.

### Task1 — MA-L: offline candidate and discriminating tests

**Interfaces:** Original generic signature is
`_equality_implies_column_bounds(problem::LinearProblem, row_terms,
pivot_column::Int, pivot::ExactValue, rhs::ExactValue)::Bool`, with
`ExactValue = Rational{BigInt}`. Preserve its entire original body. Candidate
adds the method with `problem::LinearProblem{Rational{BigInt}}` and
`row_terms::Vector{Tuple{Int,Rational{BigInt}}}`; all other arguments unchanged.
For length!=8 call the original generic by `invoke` with
`Tuple{LinearProblem,Any,Int,ExactValue,ExactValue}`. For length8 call
`_ma_equality_bounds8` with the same arguments, returning Bool. Test source uses
separate local names/modules, never overwrite production methods at runtime.

- [ ] Save exact source/reference plus an inverse map for every diagnostic rename
  and every candidate edit. The original generic method and final comparison
  block in the specialized body must be byte-identical. Record package/runtime
  source versions as read-time evidence, not retroactive MA-J launch pins.
- [ ] Write UNEXECUTED testsets `selection_boundaries`, `private_leaf_ownership`,
  `exact_bound_decisions`, `fallback_precision` and `tail_controls`. Expected
  outputs come from a separate rational endpoint-enumeration oracle, never from
  candidate output. Use protected exact BigFloat conversion (max of stored and
  ambient precision), with a deliberately lossy conversion negative control.
- [ ] Freeze finite values as canonical numerator/denominator strings and all
  expected routes before any Julia. Boundary tests cover numerator bit lengths
  128/129/130, qualifying addition ordinal1/2, trigger positions2/3/4, both signs,
  all8 pivot positions, opposite numerator signs, one/both infinite pivot bounds,
  infinity appearing before/after selection and fixed prefix then divergence.
  Include zero/unit/-1/cancellation, repeated input rational objects, shared
  numerator/denominator leaves and zero result followed by pool reuse. Enumerate
  feasible combinations in fixtures.json; impossible combinations are explicit
  exclusions, not silently fabricated coverage. Cap correctness fixtures at256;
  publish exact case/predicate counts at MA-L review before launch admission.
- [ ] Each finite boundary fixture has tight inside/equality/outside pivot-bound
  variants with independent expected true/true/false, where appropriate. Include
  both pivot signs. Infinite cases have separate explicit expected predicates.
  NonQ controls cover Float64 and stored BigFloat256/512 at matching ambient,
  plus stored256 at ambient64/512 with nonzero low bits. Custom row containers
  use the generic original; no extra length/indexability assumption is allowed.
- [ ] Implement the spec's fixed selector: original position<=3; two qualifying
  endpoint additions in min/max order; both finite live sums and unequal finite
  current bounds; nonzero summands/unequal denominators. At ordinal2 require
  matching numerator signs and both base2 bit lengths>=129, otherwise permanently
  decline. After position3 permanently decline if still inactive. Counters saturate
  at2. Reuse the original denominator test and min/max-bound equality observation;
  document any necessary extra comparison instead of claiming it is free.
- [ ] On selection initialize exactly the MA-J pool/buffer shape and use the
  source-bound private_add logic. Preserve zero/shared-product shortcuts, but
  use private_add for ALL nonzero additions after activation. Prove the live
  endpoint exclusion invariant including the state between min and max updates.
  Assert nine disjoint mutable leaves, disjoint from all input leaves, in tests.
- [ ] Use a separately saved diagnostic copy with enumerated counter/check
  insertions to observe selection position, one scratch construction, subsequent
  MA additions and private-leaf invariants. Prove inverse equality to uninstrumented
  candidate. Never time this instrumented copy; no production counters/ledgers.
  Reference is expected to fail ONLY the optimization-specific route assertions;
  numerical/input oracles must pass for it. Label offline textual RED separately
  from the later actual Julia expected failure.
- [ ] Freeze the76-case cost grid below and its fixture generator/expected routes.
  No case may be edited after numerical output. If a target cannot meet the
  fixed predicate offline, stop for a reviewed plan correction before execution.
- [ ] Run `python3 .../MA-L/source-check.py` ONCE: exact inverse, untouched generic
  and final block, all fixture oracle/route expectations, no extra traversal,
  complete IDs/counts and no actual src/test/env/CI edits must PASS. This is not
  Julia parsing or numerical qualification. Fresh independent correctness/work/
  memory review must accept the candidate and exact test counts before MA-M.

### Task2 — MA-M: bounded qualification and whole-call cost

**Consumes:** Exact accepted MA-L artifacts. **Produces:** pass/fail diagnostic
record for this single fixed predicate, never automatic production acceptance.

The cost grid has76 cases:

| Class | Fixed dimensions | Count |
| --- | --- | ---: |
| Q8 targets | numerator scale160/256/512 bits × pivot first/last × pivot sign± ×2 general denominator families |24|
| Short Q controls | length2/4/7 × general/unit/cancel/fixed |12|
| Q8 ordinary controls | fixed-large, units, zeros, cancellation, lower-only, upper-only, both-free, small-general, late-general |9|
| Q8 adversarial controls | trigger-compatible large prefix then zero/unit/fixed/cancelling tail |4|
| NonQ generic controls | Float64/BigFloat256/BigFloat512 × length2/4/8 × general/unit/cancel |27|

Total24 targets+52 controls =76. Use **76** in the frozen MA-L/MA-M inventories
and schedule; no length9 fixture is timed.
An over-cap length9 direct-helper correctness fallback is included in Task1 only,
not represented as a public aggregation case. All24 targets must activate by
position3; ordinary/short/generic controls must avoid scratch. Adversarial
controls may activate and are required to pass the same cost rejection gates.

- [ ] Freeze a concrete admission: exact source loading arrangement, fixture
  encodings/oracles/counts, executable and full import/source dependencies,
  commands, nonoverwriting output reservations, process identity/resources,
  timeout/termination reserve and fail-closed raw/exit/audit schema. Ordinary
  staged source loading only; no new full-module isolation or global overwrite.
  Bind actual loaded candidate/reference and test source by exact inverse.
- [ ] Prepare separate stage commands for actual expected optimization RED,
  candidate GREEN and cost. At most3 serial processes total, each120s INCLUDING
  shutdown, with114s run guard+6s termination reserve. First process includes
  the bounded correctness/ownership/RED checks plus cost; later processes repeat
  the same frozen cost grid and output/input checks only. Total hard cap360s.
  A timeout/failure stops the sequence; never retry/tune automatically.
- [ ] Have a fresh independent numerical/work/memory admission review accept
  exact manifests/commands and test counts. Standing human short-run permission
  already exists; do not ask for it again. Review acceptance is a technical gate.
- [ ] Execute only admitted commands. RED must fail specified scratch-route
  assertions on the original, while all exact/input assertions pass; GREEN must
  pass all. Snapshot inputs including rational leaf identities/values, all array
  owners/content, bound flags, BigFloat precision and ambient state. Check after
  every qualified call and outside each timed batch. Any mismatch stops acceptance.
- [ ] In EACH of3 processes and for EACH of76 cases run3 warm+7 measured
  alternating reference/candidate pairs,128 complete function calls per window.
  Reverse first side by process and case parity. Scratch is freshly created
  inside EACH selected call, routing and result consumption inside @timed.
  Fixed fixtures/oracles/input snapshots/serialization stay outside; retain a
  Bool result checksum. No persistent scratch, manual timed GC or discarded tail.
  Record separate first-call/import/qualification elapsed costs; not cold claims.
- [ ] Schedule totals:1520 windows/process (456 warm+1064 measured),194560 calls/
  process;4560 windows and583680 calls across3 processes. Record every elapsed,
  bytes/event count, compile/recompile and GC time; all measured compile/recompile
  must be zero. Keep all GC windows/outliers, pair order and resource records.
  Do not subtract initialization or fit thresholds from results.
- [ ] For EACH target require pooled median(candidate/reference)<=0.95, at least
  18/21 measured pairs faster, each process's median ratio<1, and strictly lower
  median allocated bytes AND events in each process. No pooled win may conceal
  a losing target. For EACH control require pooled median ratio<=1.00, EACH
  process median<=1.02, and median bytes/events no greater than reference in
  EACH process. All76 cases must pass. The2% bound permits measurement variation
  in individual processes, not a claim of a universal zero-overhead path.
- [ ] Publish ratios/ranges/MAD and process-specific medians, raw counts including
  warmup/compilation/init, exact call budgets, uncertainty and every failed gate.
  Passing these finite gates supports only “no measured regression under this
  protocol”; it cannot prove no slowdown on all possible rows/hardware. Any
  failed gate, unreliable timing or incomplete process gives NOT ACCEPTED; keep
  candidate isolated and preserve all failed evidence without retuning.
- [ ] Fresh result review independently recomputes all76 case gates and checks
  exact/input/ownership coverage and all loaded source bindings. Explicitly
  state unnecessary work/memory verdict and limits (no native-free/end-to-end
  proof). PASS closure and exact complete staged names/blobs before failfast
  commit/push of diagnostics. Master remains unchanged.

### Task3 — conditional integration handoff, not a launch permission

- [ ] Only after Task2 acceptance prepare a separate production integration plan.
  It must test actual `aggregate_sparse_equalities` reachability and output/model
  preservation for both selected and rejected rows, plus whole-pass cost with
  sparse and dense neighborhoods and existing fill/row guards. Helper benefit
  alone does not authorize an end-to-end speedup or deployment claim.
- [ ] Pin narrow changes to `src/presolve_aggregation.jl`, applicable presolver
  tests, and explicit MutableArithmetics dependency/import if required. Account
  for package/import cost and Julia version compatibility; no ambient transitive
  dependency assumption. Do not change Project.toml during this plan's component
  preparation. Define actual production RED/GREEN and reviewed integration gates
  in that separate plan before touching production or master.

## Work and memory ledger / rejection policy

Frequency is per equality-bound predicate call, potentially for each candidate
pivot of every eligible row. NonQ/container fallback retains generic body; typed
short fallback adds method dispatch/one length check/invoke. Q8 adds position/
small-counter state and inactive/active branches; current-bound equality may
need one shared local observation per early term. At most two base2 numerator
size queries and sign comparisons occur once. No extra vector/matrix scan.
BigInt comparisons and scalar arithmetic scale with limb lengths, not O(1) in
number magnitude. Installed base2 ndigits source calls GMP sizeinbase; no claim
that all native work is measured by Julia counters.

Selected calls add three rationals and three buffer BigInts with variable limb
storage, <=four endpoint identity checks per private addition and normal MA gcd/
normalization work. Postactivation same-denominator work is deliberate for safe
ownership; costly false positives are rejection cases, not an excuse to bypass
that rule. No persistent scratch/cached model references/retained pool. Temporary
memory may survive until GC; private ownership is not proof of native free.

The plan introduces no production work/memory now. Whether the proposed selector
avoids unnecessary costs is UNQUALIFIED until all control gates pass. If it fails,
stop this fixed candidate rather than extend the audit into automatic tuning.
