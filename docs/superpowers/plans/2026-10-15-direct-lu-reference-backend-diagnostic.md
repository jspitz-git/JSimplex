# Direct LU reference backend diagnostic: bounded follow-up plan

Scope: separate diagnostic of the existing sparse96 FT/native reference failure.
This is not Task 3 cost2, a performance rescue, production repair or new candidate.
Preparation and independent review come first; no execution in the source-only
step that creates this plan. Preserve all previous evidence and before mappings.

## Fixed inputs and process

Use exact tokens of sparse96 B0 through B4 and steps 1–5 from the already frozen
DIRECT-LU-COST-PREPARATION/inputs.json and matching inputs.toml. Use the qualified
ordinary overlay with unchanged source. No newly generated LP or changed RHS.
One new process, <=45 seconds inclusive, one attempt, same single Julia/BLAS,
2 GiB heap, 8 GiB VM, minimum 6 GiB available RAM, maximum 1 GiB swap guards.
No explicit warmup, timing comparison, benchmark repetition or parameter tuning.
Bind literal command, guards, manifests, reservation, raw schema and canonical
auditor; fresh refs/boot/start ticks/commands/all204groups ANDsessions/noJulia,
plus any genuinely new groups, and fresh independent stage review before launch.
Prepare fail-closed raw-before-assert output handling and whole-process deadline.

## Two fixed contexts and complete explicit call budget

1. Fresh backend: construct native UMFPACK backend directly from exact B4. Perform
   step-5 entering FTRAN, DSE FTRAN, then unit BTRAN with separate owned outputs.
   This is 1 factorization, 2 FTRAN and 1 BTRAN.
2. Original prefix: construct ordinary FT/native from B0. Execute steps 1–4 in the
   exact driver order: entering FTRAN, DSE FTRAN, replacement using saved entering
   direction, unit BTRAN; then refactor once to B4. Execute step-5 entering and DSE
   FTRAN only, no fifth replacement. Snapshot those outputs before any extra solve.
   Then call the ordinary backend directly once with the same DSE RHS into a new
   owned vector. This is 2 factorizations (initial plus refactor), 11 FTRAN,
   4 BTRAN, 4 replacements and 1 refactor. No additional workspace/public solve,
   quality/refinement/certificate calls, copies of factors or hidden orientation
   validation solves are requested.

Total: 3 factorization entries, 13 FTRAN, 5 BTRAN, 4 replacements, 1 refactor.
Retain the fresh context until both contexts finish; count up to THREE live native
factors: fresh B4 plus prefix active B4 and its retained B0 spare. The two final
metadata snapshots are a separate bound, not the native-memory bound. Future
driver preparation must inventory temporary extraction buffers, owned retained
L/U/p/q/Rs/control/Info arrays and detached outputs, as well as the ordinary FT
upper/history/prepared scratch. No inference of native deallocation from Julia
reachability; do not add GC, copy or cleanup calls to hide retained cost.
These are explicit entry budgets, not an instrumented transitive native/import
budget. Native default IRSTEP remains zero. Any unexpected dispatch/control,
count or source identity is recorded and rejects the diagnostic admission.

## Required capture and immutable oracles

Capture raw outputs and exact source/input identities for both contexts. For the
prefix record post-refactor empty history, identity maps/upper, compiled row-cache
reset, prepared invalidation BEFORE step-5 calls; after calls record ordinary DSE
and subsequent base-only DSE. Read controls immediately after construction/refactor
and after solves. Do not mutate controls, pivot thresholds or arithmetic precision.

After all planned solves in each context, take owned L/U/p/q/Rs and relevant Info
metadata via the installed UMFPACK extraction interface, plus native CSC input
identity/value checks. Inspect the exact extraction implementation during driver
preparation: forbid _hh_scale_mode or any helper that adds a solve. Preserve any
factor-info values as observed, not as proof of causal internal operations.
Inventory every captured array and scalar field, and its dimension/nonzero bound,
before accepting the driver. At most two final native factor snapshots; no growing
trace or per-solve factor snapshots. Save output tokens before aggregate asserts.

Offline auditor checks all saved outputs against the original frozen residual
formula and reports every Boolean, including expected FALSE. It compares the
step-5 prefix DSE bits with the original failed window and the fresh/direct-base
DSE results. Failure to reproduce is a valid diagnostic outcome, not retry
permission. Prefix cache invariants and immutable inputs must pass independently.

Use source-proven UMFPACK L*U = (Rs .* B)[p,q] convention, verified against the
installed wrapper documentation before driver acceptance. Exact offline arithmetic
may evaluate the factor identity and triangular equations for the two saved DSE
outputs. If scaling orientation cannot be bound without extra calls, refuse the
admission; do not choose orientation to fit data. Do not relabel a mismatching
factor representation or solve as acceptable under a different tolerance.

Interpretation: ordinary-vs-base equality localizes wrapper effects; fresh-vs-
refactored differences discriminate lifecycle dependence. L/U identity residuals
and triangular equation residuals can separate recorded factor representation
from application consistency, but do not identify the original native operation
without supporting evidence. Keep ambiguity explicit. Diagnostic acceptance means
faithful bounded evidence, never cost qualification or solver-wide correctness.

## Preparation, review and closure

Prepare separate driver, immutable required-path inventory, exact command/guard,
raw auditor and offline failure tests. Independently review numerical semantics,
ownership, explicit budgets, all new scans/copies and retained memory. Preserve
failed preparation/review artifacts and use separately named fixes if needed.
Only after accepted concrete preparation may a new exact stage be sealed and
reviewed. Existing standing permission for short numerics does not bypass that
gate; no repeated user permission question is needed once the gate is satisfied.

After a future attempt, preserve original exit/raw/false gates, independently
review the diagnostic result, verify process closure and pins, and publish exact
names/blobs after a separate PASS closure. No automatic repair, cost2, promotion,
merge to master, second attempt, full suite or long benchmark follows.
