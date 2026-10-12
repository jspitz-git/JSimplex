# S4-S: isolated solver-core module loading contract

Source/evidence only at diagnostic398f0e6 / master0eb75c3. No Julia, module loading,
macro execution, native calls, compilation, factors, workspaces or solver calls occurred.
The result is ONE conditional, byte-invertible OFFLINE loading proposal. It qualifies
source isolation under the explicit resident-dependency preconditions below; it does
not prove runtime loading, method identity, public trajectory or numerical correctness.

## Concrete namespace and complete file manifest

`results/S4-S/manifest.json` enumerates the original70-file depth-first include closure,
the selected64-file closure and all128 side/path/order/source-hash/proposed-hash entries.
The proposed fresh containers are `Main.S4HHReference` and `Main.S4HHCandidate`, each
containing a child named `JSimplex`. They MUST NOT already exist. The two proposed trees
are `reference/src/...` and `candidate/src/...`; relative include resolution must stay
inside the corresponding materialized tree, whose hashes are checked before any load.
A future loader would include each root into its fresh container, not into production.
No runnable tree or loader was installed in S; two changed bodies are saved as `.txt`.

The reference and candidate root have exactly seven identical substitutions:

- Each of the three `using LinearAlgebra/Logging/SparseArrays` lines becomes a constant
  binding to `Main.JSimplex.<dependency>` followed by `using .<dependency>`.
- `import OrderedCollections` becomes a constant alias to its resident production module.
- The PrecompileTools import, MOI include and precompile include each become an explicit
  exclusion comment. No preference/global flag is changed or relied upon.

All other selected reference files are byte-identical to current production. The candidate
has ONE additional substitution in huangfu_hall_factorization.jl: the Float64 `lu!`
`reuse_symbolic=false` becomes the already qualified pattern predicate on the same-type
CSC conversion. There are ZERO renamed function routes. Types and internal generics live
in each new child module, so the real local factory/refactor dispatch naturally uses the
candidate helper. The shared UMFPACK type is only an argument of a newly owned helper;
no method on `lu!` or another native generic is added. The manifest records every exact
old/new string, counts and hashes; reversing them recovers the original bytes exactly.

The child retains the name JSimplex. Thus the executable self-reference in solver.jl494
resolves to that child, not Main.JSimplex; no solver-body substitution is necessary.
Imports inside source documentation examples are text, not executable imports. MOI's
`pkgversion(JSimplex)` reference is in the excluded integration. Original-model copy,
feasibility, cleanup/retry, objective restoration and acceptance bodies are unchanged.
No working-model certificate is promoted to original-model evidence.

## Imported method ownership

The saved inventory lists all62 explicit qualified definitions in the original closure
with complete signatures and lines (including annotated and multiline definitions).
29 remain selected, all on Base generics and all containing a newly defined nominal type:

| Type owned by each new child | Explicit selected methods |
|---|---:|
| Bound | 4 |
| _UnreliableBasisSolve | 1 |
| IndexedVector | 1 |
| MPSParseError | 1 |
| _UnitTransposeRHS | 3 |
| UpperRowIndices | 13 |
| DiagnosticObserverFailure | 1 |
| _PriceAuditMatrix | 2 |
| _PrimalActivityBounds | 3 |

The remaining33 explicit methods belong to MOI integration and contain local Optimizer;
these are all excluded with moi.jl plus its four children. They are not claimed to be
unsafe signatures: excluding the unused integration avoids another dependency-loading
boundary and the nested module's package-version semantics. Public `solve` qualification
will NOT be MOI qualification or a test of the untouched installed package module.

Four @enum types (TerminationStatus, ObjectiveSense, VariableDomain, VariableState) also
add five external families EACH: Enums.namemap, Base.typemin/typemax, Enums._enum_hash and
Base.instances. Installed Enums.jl shows every generated signature owns the new enum type.
Its type-expression evaluation resolves UInt8; these enums have no custom value expressions.
These20 generated signatures plus29 explicit ones are not62 executed/observed method calls.
@kwdef defines the local SolveStatistics constructor; constprop/inline/noinline/propagate
annotations do not invoke solver bodies. Documentation and ordinary function-body macros
do not execute their example/solve bodies during module loading.

Keyword lowering adds further implicit entries: `Base.sizehint!(::UpperRowIndices,...;
kwargs...)` creates a Core.kwcall method whose positional arguments still contain the
fresh UpperRowIndices type, plus a local keyword body. Other local keyword functions
and @kwdef constructors dispatch through their fresh callable/type identities. These
lowered methods also consume method-table/JIT metadata. The29 explicit plus20 enum
signatures are therefore NOT a complete runtime method count; no keyword-lowering
method table was captured. Fresh owned dispatch prevents the identified keyword routes
from replacing the corresponding production methods under the same preconditions.

No coincident explicit/generated external signature was identified in this pinned closure.
Adding disjoint methods still mutates shared Base method tables and can incur invalidation
or compilation; it is NOT a claim of no global effects. Main's production types remain
separate and no production method is overwritten. This rests on fresh namespaces, no
unlisted imports/eval/substitution and exact materialization. The offline scanner is
format-specific and is backed by manual inspection of macro/definition forms, not a
Julia parser or runtime method-table capture. Later hash drift invalidates this contract.

## Loading work and explicit exclusions

Installed PrecompileTools1.3.4 (Manifest and installed Project agree) uses the condition
`iscompiling || verbose[]` in BOTH workload macros. Its source includes a ccall checking
output generation and inference-tagging calls. Therefore a cache-only comment or default
preference does not establish zero workload for every load. The proposed roots remove
both import and precompile.jl include, without changing package preferences. The original
precompile.jl, its public/native workloads and bytes remain preserved and excluded.
No upstream download or installed-build equivalence claim was needed.

The source-only ZERO hidden numerical-call conclusion is conditional on Main.JSimplex
and its four dependency modules ALREADY being resident and pinned. Constant aliases plus
relative `using` bind those existing modules; they do not request a new package by name.
The proposal performs no `using JSimplex`, `import MathOptInterface`, dependency bootstrap,
package installation or cache build. A future driver must verify these preconditions and
refuse absent/mismatched bindings; it must not silently load missing dependencies.
Initial process/package bootstrap is separate required setup, NOT proved numerically
empty by this contract. A future overall work budget must account for it or reject launch.

The remaining64-file closure uses literal includes, declarations, local constructors,
owned-type extensions and finite constant setup: enum/name metadata, tuple/symbol tables,
type aliases, a regex and documentation. HYPERSPARSE_KERNEL_KEYS builds18 symbols by
nested ntuple; SIMPLEX_KERNEL_KEYS flattens them. The MPS regex may compile/cache native
PCRE data. Parsing, type/method registration, allocations, metadata, macro expansion and
possible JIT are real setup work, NOT zero work or zero native-runtime activity. There
is no top-level numerical factor/solve/workspace call in the selected source. The two
explicit MPFR ccall sites remain inside Markowitz functions, not executed top-level.
No custom module __init__, dynamic include, @eval or direct eval occurs in this closure;
Base enum macro's bounded type evaluation is separately accounted for above.

Two module copies retain separate types, methods, documentation, enum dictionaries,
constant metadata and future specializations until process exit. External dependencies
and native libraries remain shared, not privately copied. Input LP/options must later be
reconstituted for each module's own types from frozen identical scalar bits; cross-module
model objects cannot be passed as though their nominal types were identical. No adapter,
per-solve forwarding, factor copy or diagnostic state is added by this source proposal.
Actual setup/JIT/retained bytes and invalidations are UNMEASURED. This seam is for a
numerical integration qualification, not an end-to-end cost comparison.

## Acceptance boundary and next action

Source isolation is supported for this explicit reduced solver-core manifest under the
resident-dependency/fresh-namespace conditions. Runtime loading remains UNEXECUTED. A
future pre-solve identity/materialization check is necessary; if it fails, preserve the
attempt and stop without retry or extra warmup. No source qualification authorizes a
numerical launch or proves a public refactor is reached. No production/test/env/master/CI
change or old script/cost rerun was made; no unnecessary production work/memory introduced.

ONE next action is S4-T source/exact-offline public LP and complete work contract. Freeze
one new small finite nonsymmetric LP with an exact original feasible/optimal witness;
derive eligible refactor reachability and all setup/phase/recovery/cleanup/certificate
attempt caps, including bootstrap and any instrumentation changes. Reject an unbounded
path rather than run it to discover counts. No need to redo this include inventory or
R's controller map. Q remains unchanged: GC-dominated outer windows, preserved unexplained
outlier, no consistent inclusive speedup. Native retention and broader S4/S6/control/
scalar/platform/fullsuite stay OPEN, HH reuse disabled, CI off, all rejections unchanged.
