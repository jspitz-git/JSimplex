# S4-C: exact Markowitz HH triplet allocation

Status: integrated and pushed. Production0f2c468 -> master3220118. Baseline production master b720674; diagnostic
base ab68ceb. Only `_hh_extract_parts(::MarkowitzBackend, ::HHExtractWorkspace)`
changes. The frozen reference is the previous method, renamed for diagnostics.

## Numerical and ownership contract

The candidate counts exact temporary lengths, allocates six coordinate/value
vectors once, then fills them in the original order. Packed sparse entries,
including stored zeros, are copied unchanged; dense-core entries use the original
`iszero` predicate. CSC assembly, permutations and independent owned outputs are
unchanged. No tolerance, scalar type, factor arithmetic or cache changes.

RED triplet-red-1: 440 exact-output checks pass and the intended allocation gate
fails (7,356,880 bytes on both sides). GREEN triplet-green-1: all442 checks pass,
3,705,352 candidate bytes vs7,356,880 baseline bytes, measured compilation zero.
Exact CSC structure/values/permutations and output ownership cover Float16/32/64,
BigFloat and Rational{BigInt}, empty/singleton/sparse/dense/pivoted/tiny/zero cases.
Existing focused HH suite passes4366/4366, including scalar integration, precision
transfer, failed refactorization isolation and saved factor behavior. Exit0 and
independently recomputed source/environment pins accepted. The focused suite is
not a full repository/S6 test gate.

## Computational work and memory

Frequency: setup/refactorization extraction, including recovery refactorization, no added ordinary-iteration or
candidate work. Added O(sparse_pivots) length reads and one O(core_dimension^2)
zero-predicate traversal. Removed dynamic growth/copy traffic in six temporary
triplet vectors. Dense core is read twice but never materialized again. Temporary
lengths are exact, avoiding full-triangle reservation for mostly-zero cores.
No new retained cache, invalidation protocol or solve. Existing CSC constructors
and output copies remain. Shared `one(T)` for the lower diagonal matches the
original fill semantics; no mutable scalar is modified by this method.

## Paired cost evidence

triplet-cost-1: seven Float64 synthetic fixtures, six alternating pairs per fixture,
16 extractions/sample,84 samples, compile0 throughout. Warmups are separate;
GC and elapsed are recorded separately (elapsed includes GC). All14 post-exit audit
checks pass, including complete pair keys/order, finite metrics, pins and source.
Raw reports remain under `.superpowers/simplex-core-architecture/S4-C/` and portable
reports under `results/S4-C/`. Allocation bytes/events are per16 calls below.

| Fixture | Baseline bytes | Candidate bytes | Baseline events | Candidate events | Median time ratio | Paired ratio range |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| dense256 | 1.1771e+08 | 5.92856e+07 | 2640 | 1200 | 0.6258 | 0.4561–0.6565 |
| dense64 | 6.47514e+06 | 3.83053e+06 | 1744 | 1024 | 0.6707 | 0.3312–1.4771 |
| mixed64 | 1.91411e+06 | 1.1584e+06 | 1456 | 1024 | 0.7957 | 0.6088–1.7107 |
| mostly_zero_core256 | 1.03718e+06 | 852096 | 1392 | 1200 | 1.0258 | 0.9783–1.0760 |
| mostly_zero_core64 | 281856 | 230400 | 944 | 800 | 0.9225 | 0.8868–0.9539 |
| sparse256 | 1.46176e+06 | 1.18874e+06 | 1456 | 1168 | 0.8981 | 0.8513–0.9499 |
| sparse64 | 429184 | 318976 | 1040 | 800 | 0.6244 | 0.5712–1.1088 |

The table ratio divides side medians, while paired ranges use matched individual
samples. Mostly-zero core256 has side-median ratio1.0258 and paired-median1.0088
(range0.9783–1.0760). This is a small explained counting-pass tradeoff with
substantially overlapping timings, not evidence of elapsed savings on this shape.
Dense256 side-median ratio0.6258 is supported by all six faster pairs, but the
small/mixed cases have noisy individual ratios; no universal speedup is inferred.
All seven fixtures allocate fewer bytes. Mostly-zero cores use an explicitly
constructed valid LU(identity) core representation, not a backend-selection claim.
Cost matrices differ from the earlier periodic component-attribution fixtures;
absolute timings must not be cross-compared as identical inputs.

Ruling: retain exact counting rather than reserving full dense triangles. The
extra scan is explicit and bounded to extraction, while allocation reduction is
consistent. Cost if wrong: mostly-zero large cores can pay a small elapsed penalty;
large-core/cross-precision cost and whole-medium performance remain unmeasured.
Resource peaks: VM739736KiB, sampled RSS424572KiB, available RAM minimum22482404KiB,
swap0. No repeated accepted native/component or long baseline measurement.

## Acceptance and integration

Eight paired whole-solver trajectories with forced sparse/dense modes and
refactorization_interval=3 passed121 assertions. Exact entry/final/event hashes,
iterations/refactorizations/kernel counts match on all pairs. All9 post-exit audit
checks pass, including source hashes and independently reverified pins.
Fresh independent gpt-6-astra review approved bounded integration without blockers
or numerical concerns. It independently confirmed the frozen baseline method,
count/fill agreement, source hashes and exact paired records. No unnecessary work
or retained-memory increase was found within the exact-allocation approach. Cost
is O(k+c²) and does not scale with update-chain length. No declined numerical case
requires a waiver; broad whole-solver speedup, large-core/cross-precision cost and
full repository correctness are explicitly outside this local gate.
Separate production0f2c468 is integrated as master3220118 and pushed; remote ref
verified322011855af909d0d93b6f9bbecbe4200512fc67. Master integration passed1294/1294
(852 existing backend tests +442 exact/allocation checks), exit0,all7post-exit
checks,independent pins,actual package-source assertion and main user-file hashes.
Runner358060/child358061/driver358052 separately absent; no Julia at closure.
No deferred minor findings.
Broader S4/S5/S6 and the historical medium/full-CI failures remain open. CI stays
disabled at the user's request.
