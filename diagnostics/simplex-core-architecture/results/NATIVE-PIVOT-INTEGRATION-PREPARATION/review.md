# Independent offline integration preparation review

Not accepted pending one documentation correction. No Julia parsing, import,
compilation, solver execution, old checker execution, staging or production edit
occurred in this review. This is preparation review, never numerical admission.

## Finding

WORK-AND-ADMISSION.md, Added cold memory and retained state, describes seven public
input snapshots, seven copied objects and nine buffers. The literal `inputs` tuple
in native_pivot_integration_tests.jl contains six objects: one CSC matrix, objective,
and four bound vectors. `map(copy, inputs)` therefore copies six objects with eight
backing buffers (three CSC buffers plus five vectors). The 23 entry count and 184
cumulative entries across eight calls are correct. Correct the object/buffer counts
and preserve this initial review before rebinding the revised preparation evidence.

## Independently checked evidence

The new exclusive reviewer-offline-check.py produced reviewer-checks.json: 372
checks, only the stated ledger check failed. Fresh readtime preparation-pins has
833 matching hashes, source-check has 12 true checks and 91 matching hashes,
author-check has 12 true checks, and all 520 actual-baseline entries match current
files and HEAD. HEAD fac3ffc1065f9c34852ce82a6d33b496aa641936, master
6f68e24e8ddac42b948da8fcc2d636c010751194, branch and clean tracked index are unchanged.
The old 75 overlay records and all seven production replacements remain exact;
the new 76th record is solely the focused integration test. The candidate runtests
copy reverses exactly to the original with its two added includes removed.
All six observation edits apply in declared order and invert to the whole accepted
factorization source, including both empty and nonempty refactor returns.

Accepted GREEN2/cost audits and reviews, their direct sha256/evidence bindings,
postcheck, and cost closure/publication bindings were freshly validated. All four
continuation mappings resolve to preserved predecessor bytes. GREEN2 remains 6977
assertions including 119 serialization regressions. Cost remains 2112 selected
policy passes and 176 default DSE-FTRAN failures, with two GC windows and all old
outliers preserved. Original failed GREEN remains failed. No historical program
was imported or rerun. Supplemental finalize.py/publication.py/continuation text
were read only; closure and exact publication are separate actions.

## Numerical correctness and coverage

The eight real public solve calls preserve the specified 3x2 LP, original native
legacy dual/steepest-edge settings, interval 2, time 5, iteration limit 100, and
literal OPTIMAL/[2,2]/-10 oracles. No tolerance, safeguard, precision, model or
certificate change is introduced. Public endpoint assertions alone cannot detect
policy routing lost on an easy LP; the documents accurately require an independent
all20 expected-control probe at construction/refactor before any numerical admission.

The private PFI Float64 recovery uses the original 1x1 fixture and exactly one
initialize, explicit checkpoint and _recovery_trial, with no publish/restore.
Its 29 assertions preserve live owners, control bits, selected arrays and checkpoint
values while allowing precisely the existing consumed refactor increment. They
check private manager/backend/native/control ownership and selected policy. Comparing
trial/live controls is an appropriate retention oracle combined with previously
accepted Task1 independent controls tests; extra literal pivot/IRSTEP assertions
would be optional duplication, not required to satisfy this preparation contract.

Five option comparisons iterate all 17 fields, including phase, remaining budget,
auxiliary settings and Float64→BigFloat256→Float64 intent. They make six copy-function
calls and do not factor/solve in BigFloat. Static prospective count is
8*6+29+5*17=162, conditional on successful completion; runtime remains unqualified.

Source inspection of initialize/recompute/recovery and NumericalPolicy confirms
recovery requests 2 constructions, 2 F and 3 B entries, with at most three conditional
weight correction B entries. refine_basis_solve! enters its correction loop even
when native solve_refinement is false; the documented 3..6 B range is therefore
appropriately conservative. Public internals remain dynamic. Caps
514/512/32770/32774 are arithmetic sums of the proposed case limits, not observed
counts or proven complete-controller/native bounds. Extracted triangular operations
and raw auxiliary LU are explicitly excluded from the UMFPACK backend seam.

The seams are honestly unimplemented data. Before ONE integration attempt, a
separate offline concrete probe/driver/guard/auditor/resource contract must establish
case boundaries, attempt/success counters, throwing paths, empty handling, immutable
raw output, cap enforcement and failure provenance, then receive fresh exact-stage
admission. No refactor coverage is manufactured. Source-only reused recovery tests
are not represented as executed GREEN2 coverage. This review authorizes no launch,
production merge, direct prototype change or old cost2 continuation.

## Computational work and memory

No unnecessary NEW production work or retained memory was found: the seven source
replacements and previous overlay are byte-identical. Consequently this step adds
zero production scans, basis solves, matrix copies, conversions or policy checks at
setup, refactorization, iteration, candidate, recovery or certification frequency.
New test work is cold: public input snapshots cover 23 entries per call; recovery
snapshots cover 44 entries plus the original five-container, nine-entry checkpoint.
Selected owner tuples retain live/trial references for the test's lifetime; no
native deallocation claim is made. Expected arrays, comparison/Test storage and
original solver/factor/quality work are additional, as documented. The only defect
is the six-object/eight-buffer accounting above, not avoidable computational work.
Future successful-factor callbacks would scan 20 controls and use fixed storage;
those diagnostic costs must be counted separately from production work. No timing
or allocation measurement is justified for unchanged production/cold offline text.
Prior fill/cost tradeoffs are not generalized into a universal speedup claim.
