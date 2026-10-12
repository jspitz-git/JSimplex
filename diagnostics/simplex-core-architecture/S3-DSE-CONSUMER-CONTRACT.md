# S3-C: DSE support consumer contract

SOURCE/EVIDENCE ONLY. No solver, module loading, compilation, native call, new LP
calculation, old audit or numerical rerun. Current production is unchanged from
master 0eb75c3. S3-A/B remain accepted within their recorded scopes.

## Decision

The current DSE recurrence consumes dense values, not support indices. Exact support
is a solve-routing contract; it does not authorize skipping zero-coefficient rows.
No production defect is established. One concrete composition remains unqualified:
**a nonempty-history entering-column FTRAN followed by a differently routed DSE
weight FTRAN, then replacement using the original direction**. Existing component
provenance rules explain the expected behavior, but the reused evidence does not
capture this mode pair together with its DSE weights and prepared-state transition.
A narrow prospective qualification is specified separately; nothing is launched.

## Call and ownership boundary

`dual_simplex.jl:602-615,670-692,1435-1442`: after primal/dual value updates and before
column replacement, `update_dual_pricing_weights!` calls `update_dse!` when steepest
edge remains selected. It computes entering_weight = squared_norm / pivot^2, solves
B*tau = rho through `_checked_basis_solve!` with operation `:weight_ftran`, then
visits every basic row in enumeration order and applies exactly the existing
parenthesized recurrence and typed 1/10000 floor. It finally writes the entering
weight. No zero-coefficient skip or sparse reduction replaces this loop.

The six pipeline value owners are row_rhs, row_solution, rho, tau, tableau_row,
pricing_row. Support wrappers borrow these vectors; they own indices/membership.
Normal DSE uses distinct rho input, tau output and the already-produced tableau
column. An arbitrary caller supplying overlapping vectors is not thereby given
an alias-safe DSE API: update_dse! itself does not validate arbitrary aliasing.
Generic solve/private-buffer checks and S3-A overlapping-write invalidation remain
in force; they are not permission to make a DSE tableau column alias tau.

The checked solve first performs the pipeline solve inside the FTRAN timer, then
conditionally refines. An accepted correction invalidates destination support;
the immediately following DSE loop reads corrected dense tau, without consuming
possibly stale support. A later support user must rebuild. A failed checked solve
throws before the DSE weight loop; upstream value writes/staged sharing are outside
this local atomicity claim. No whole-iteration rollback is asserted.

## Support, manager and arithmetic behavior

| Route | Source behavior relevant to the additional FTRAN |
| --- | --- |
| PFI | Ordinary forwarding has no triangular prepared-spike slots. Indexed support propagates through base and eta history; dense fallback remains possible. |
| FT/SS/BG, hypersparse off | `_ordinary_forward_solve!` keeps the two-slot eviction schedule but omits prepared payload copies. An earlier prepared direction can be evicted; preservation forever is not the contract. |
| FT/SS/BG, hypersparse on | Indexed output invalidates destination provenance; dense branch uses public prepared FTRAN. The `prepare_update` argument controls only the hypersparse-off branch. Mixed routing can therefore change preparation/reconstruction work. |
| HH, hypersparse off | Ordinary FTRAN leaves prepared_partial/direction unchanged while using private work/auxiliary. |
| HH, hypersparse on | No indexed HH kernel. Nonempty input falls back to dense public FTRAN, including preparation copies. DSE can replace the previously prepared payload; replacement checks supplied direction values and reconstructs when unmatched. This is already existing behavior, not a reuse defect proved here. |

Triangular reuse requires destination identity plus `isequal` values, including
signed zero. HH uses its own finite/value matching and reconstruction, not the
triangular identity rule. Refactor/update invalidation and history order remain.
No transfer of working-model acceptance to original-model certificates follows.

Empty pipeline mode writes a zero output and performs no factor solve. Nonempty
support retains every exact nonzero, however small; compaction removes exact
cancellations. Both signed zeros are absent from support, so support equality is
not a bitwise-zero-sign oracle. Full support or unavailable sparse kernels can
select dense execution. Dense output must rebuild/validate support; immediately
canonical indexed/empty output uses S3-B's length-only consumer. Exceptions leave
owned output support invalid. Mode-specific arithmetic is existing arithmetic:
S3-B old/new equality at a fixed mode is not proof of sparse/dense bit equality.

Float32/Float64, BigFloat, Rational{Int64}, Rational{BigInt} all reach the generic
DSE recurrence. BigFloat pipeline solves retain stored factor/RHS precision in
their scoped precision helper; the DSE recurrence itself has no new setprecision
scope. Fixed-width exact overflow can fail; no wider type or tolerance change is
implied. Sparse storage, native/dense fallback and BigFloat precision discovery
retain their existing conversions/scans. No general allocation-free claim follows.

## Existing evidence, without rerunning it

The saved S3-B focused run has 10645 passes and one preserved missing-fixture
error. Its completed solver group has 880 assertions: four non-HH managers,
five precisions, primal/dual, three pricing choices, Markowitz. The separate HH
supplement has 480 assertions across five precisions, both backends/algorithms
and three pricing choices. These check final certificates and route diagnostics;
they do not record the selected mixed pair or every intermediate DSE value.

The saved trajectory driver uses steepest edge and records pricing_weights in
entry/final and completed-pivot hashes. Its 80 old/new Float64 pairs cover all five
managers, both backends/algorithms, two fixtures and both forced modes. Each run
forces the same mode for ordinary and weight operations; it does not explicitly
qualify switching between those two calls. The driver does not establish the
actual mixed transition in the adaptive focused run. Public certificates remain
valuable integration evidence; they do not substitute for the selected local oracle.

Current/historical hash comparisons are recorded individually. The main pipeline,
DSE, triangular and recovery sources and solver/HH supplement tests match the
focused launch inventory. The full HH source differs (later accepted S4 changes),
and the trajectory driver was not in the earlier focused inventory. Do not label
all current code as byte-identical historical execution. Its own trajectory pins
and saved process/log are separately bound. S3-A's view/observer invalidation and
S3-B's 1900 producer cases are reused; no claim of new execution is made.

## Existing work and memory by frequency

At each reached DSE update: one pipeline FTRAN entry (zero backend solves if
empty). If solve_refinement is enabled, the checked wrapper assembles the current
basis with `_basis_matrix!` and copies the m-entry RHS into owned quality scratch.
It evaluates initial quality, optionally an additional Float64 compensated/wide
quality check, then attempts at most max_refinements ordinary correction FTRANs.
Each attempted round scans correction finiteness, constructs the m-entry trial,
and scans trial finiteness. It has up to three trial-quality evaluations when
homogeneous cleanup is proposed and then rejected. Quality evaluations traverse
basis coefficients/vector entries; cleanup adds up to two coefficient passes and
O(m) bookkeeping/norm scans. Conditional copies retain the pre-cleanup trial,
restore a rejected cleanup, and publish an accepted m-entry correction. Publication
invalidates support and emits the existing correction event. No new factorization
is added by this helper. Owned RHS/trial/correction/singleton and row/column quality
buffers are allocated lazily and retained, O(m) scalar entries besides the assembled
O(m+nnz(B)) basis; wide scalars carry precision-dependent storage. These are local
source bounds, not measured call totals or a whole-controller budget.

Input support costs O(s)
compaction when valid or O(m) reconstruction when invalid. Dense output costs an
O(m) rebuild; canonical indexed/empty output avoids the second compaction. The
DSE loop performs m weight writes plus the entering write; zero rows still incur
arithmetic/floor evaluation. The ordinary successful wrapper then scans primal,
reduced_costs, costs and weights, up to four length-(m+n) scans with short circuit.
Invalid-weight recovery may scan/reset weights, perform Devex's tableau-row scan
and m-row recurrence, and revalidate. These are required existing checks.

Each factor solve also traverses its actual base/update representation: PFI eta
entries, triangular row updates/upper columns, HH lower/upper and packed update
entries. Dense vector passes and preparation copies remain mode/manager dependent.
HH prepared FTRAN copies two m-vectors; ordinary omits them. Triangular Float32/64
slots retain up to four m-vector payloads, created/resized lazily; ordinary calls
still advance eviction. BigFloat/exact triangular preparation uses generic no-op
hooks. Pipeline support metadata is O(m+n) alongside six borrowed buffers; lazy
factor/row graphs scale with coefficient storage, not merely active support.
DSE introduces no fresh tau vector: scratch.tau is owned workspace storage.
Arithmetic on BigFloat/rational scalars can allocate; exact byte/retention totals
are not established by source. No benchmark or speedup claim is warranted.

This documentation adds no production work or memory. The next qualification
must report diagnostic snapshot/counter overhead separately and must not turn
prepared-cache lifetime or skipped floor work into an alleged optimization.

## Limits and continuation

Only the mixed DSE producer/consumer composition above is selected. The next plan
is `2026-10-12-dse-mixed-route-qualification.md`; first freeze finite inputs and
complete attempt accounting, then obtain review before any later guarded launch.
No old mode-selection census or generic factor lifecycle repetition. Broader S3,
S4 bootstrap/cache/init/whole-public caps/native retention, S6/fullsuite and all
rejected candidates remain open/unchanged. HH symbolic reuse and CI remain off.
