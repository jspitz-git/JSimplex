# Runtime follow-up: basis updates and Markowitz search

Scope approved by the user: three sequential optimizations without changing
numerical behavior. The baseline includes the earlier uncommitted runtime batch
in `runtime_audit_report.md`; its exact source hashes are the `after_source_hashes`
in `runtime_before_after.toml`. Incremental probes record both complete source trees.

## Changes

1. FT, SS and BG reuse a packed-column position between reading an entry and
   replacing or deleting that entry. No position survives a structural mutation
   of its column. BG retains its row-incidence bookkeeping.
2. FT/SS build a private row-to-column index once per sufficiently long, sparse
   update. The lists contain only ascending trailing columns. Elimination changes
   only the target row, which is excluded from this index, so the lists remain
   valid until the update ends. SS includes columns beyond the spike endpoint.
   The index is built lazily at the first nonzero multiplier; spans below 16 or
   average stored column lengths above span/4 keep the original range traversal.
   This structural heuristic affects traversal cost only, never arithmetic.
3. Markowitz retains raw column maxima during one pivot search. Singleton,
   doubleton and general candidates retain their distinct threshold helpers,
   traversal order and tie handling. Every nontrivial pivot search clears cache
   validity. The final column scan consumes prior maxima but does not store new
   ones because no later scan needs them. BigFloat maxima retain stored precision.

New storage is private to each factor/workspace. Copies do not share scratch.
Row-index buffers and maximum storage retain their established size/capacity after
smaller refactorizations. The first use allocates storage; warmed rebuilding of
row incidence allocates zero bytes.

## Measurements

All timing probes alternate old/new order, run after compilation, compare complete
source snapshots, and run without concurrent Julia test/benchmark processes.
These are kernel measurements, not a claim about complete solver speedup.

- `basis_runtime_step1.toml`: position reuse alone. Dense n=128/512 replacements
  measured about 1.21–1.23x for FT/SS and 1.15–1.16x for BG.
- `basis_runtime_step2.toml`: row incidence relative to step 1. Band n=128
  measured 2.06–2.13x and n=512 measured 6.45–6.52x for FT/SS. These measurements
  include first-use index allocation (about 11.8 KB / 46.9 KB respectively).
  Short/dense cases and unchanged BG controls include timing noise; small
  percentage changes are not evidence of a speedup.

- `markowitz_runtime_step3.toml`: 31 paired samples of ten warmed calls.
  A search stress case with many rejected singleton rows in the same column
  measured 7.12–7.19x for Float32/64, 6.71x for BigFloat and 3.00x for
  Rational{BigInt}. Those repeated rows make this a singular-system stress case,
  not a representative nonsingular basis.
  Separate **nonsingular** block triangular bases with rejected singleton rows
  in distinct columns measured full-refactorization speedups of 1.089–1.115x
  for BigFloat and 1.085–1.092x for Rational{BigInt} (roughly 8–10% less time),
  with lower allocations. Float32/64 gains in these cases were negligible.
  The other 23 complete refactorization controls ranged 0.952–1.022x:
  common cases do not show a general speedup, and extra cache checks can add
  a few percent overhead. Their warmed allocated bytes were unchanged,
  including zero bytes for native float refactorizations.
  All **1,151 assertions** passed, including exact factors, permutations and
  forward/transposed solves before and after the repeated refactorizations.

## Numerical verification

- `basis_runtime_combined.toml`: **432 exact comparisons** of packed factors,
  column permutations, update histories, forward solves and transpose solves;
  Float32, Float64, BigFloat and Rational{BigInt}, all three update methods,
  diagonal/band/dense factors and full/partial spike reach. Its 27 paired timing
  cases add **810 assertions** for exact factors and zero residual compilation.
- `runtime_three_steps.toml`: **1,152 identical recorded states across 192
  configurations**, plus **32 identical complete Float64 solver outcomes**
  (status, objective/primal, message, iteration and refactorization counts).
  Comparisons use `isequal`, including signed zeros, rather than tolerances.
- Complete solves measured a median 1.008x, range 0.940–1.054x. Unchanged
  parse/presolve controls ranged 0.943–1.058x. This run does **not** establish
  a general whole-solver speedup for these three additions. Its complete-solve
  configurations use PFI/BG; FT/SS gains are measured separately above.
- All recorded residual compilation times were zero. The combined basis,
  Markowitz and whole-solver artifacts identify the final 30 source files by hash.

Production suite: **224,921 passed** in one complete invocation (9m29.9s).
Development/JET suite: **456 passed**, including six new checks for FT/SS update
inference and cached Markowitz refactorization. No existing allocation limit
was relaxed. The new production tests contribute 974 assertions.

Independent source review found no blocking or important issues. Its requested
explicit short-spike SS coverage was added, including an indexed entry beyond
the spike endpoint. All temporary source snapshots form a consistent hash chain
from the earlier first batch through steps 1–3 to the final aggregate probes.

Verification commands:

```sh
JULIA_DEPOT_PATH=/tmp/jsimplex-precommit-depot:/home/jspitz/.julia \
  julia --startup-file=no --compiled-modules=existing --project=dev \
  -e 'push!(LOAD_PATH,pwd()); using JSimplex,Test; include("test/runtests.jl")'
JULIA_DEPOT_PATH=/tmp/jsimplex-precommit-depot:/home/jspitz/.julia \
  julia --startup-file=no --compiled-modules=existing --project=dev dev/tests/runtests.jl
```

## Reproduction

From the repository root, with the source snapshots to compare:

```sh
JULIA_DEPOT_PATH=/tmp/jsimplex-precommit-depot:/home/jspitz/.julia \
  julia --startup-file=no --compiled-modules=existing --project=dev \
  diagnostics/basis_runtime_probe.jl BEFORE_SRC OUTPUT.toml [AFTER_SRC]
# Same arguments for diagnostics/markowitz_runtime_probe.jl and runtime_probe.jl.
```

The checked-in TOML files identify snapshot contents by SHA-256 for every source
file; temporary snapshot paths are local to the original measurement session.
