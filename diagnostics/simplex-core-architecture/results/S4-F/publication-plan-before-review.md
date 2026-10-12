# S4-G: HH symbolic candidate publication and saved-state qualification

After S4-F independent acceptance, NEW bounded diagnostic qualification; no
production/test edit and no old measurement replay. Component equality is not
HH integration proof. First construct a diagnostic source clone of the exact
HH refactorize! and _hh_refactor_backend/_hh_refactor_lu! functions; use distinct
names, no method overwrite. Offline source/token diff must prove only routing
names and the Float64 lu! reuse keyword differ. Candidate uses the existing
_same_umfpack_pattern on the converted input before mutation. The reference
calls actual production refactorize!. Existing extraction/scaling/safeguards,
failure catch/discard, publication/update-retirement/prepared invalidation remain
identical. Do not silently simplify construction or rollback logic.

## Exact two lifecycles

Float64 native Int64, one reference then one candidate, independent owned data.
B0=[4 1;1 3], all full canonical CSC. Each lifecycle:

1. Actual HuangfuHallFactorization(B0) once. FTRAN for new column[5,1], then actual
   replace_column! at1: B1=[5 1;1 3]. Copy factor ONCE: saved contains this update.
2. FTRAN for new column[6,1], replace_column! at1: B2=[6 1;1 3]. Live owns a private
   suffix while saved shares its immutable prefix. Snapshot saved base/history,
   ownership and expected B1 outside all measured calls.
3. Refactor live to B3=[7 1;1 3], production or candidate as above. Native symbolic
   reuse expected only for candidate. Old backend owns the B0 CSC; guard compares
   that owned pattern, not the updated B2 values. Verify publication, empty live
   history, prepared invalidation and private/shared pool invariants. Mutate the
   separate caller B3 CSC arrays after refactor; preserve owned B3 for checks.
   One forward and one transpose solve on liveB3 and savedB1 (4calls).
4. FTRAN for[8,1], replace_column! at1: B4=[8 1;1 3]. FTRAN for current column2
   [1,3] prepares a valid direction. Own tiny snapshots of live base/history/
   prepared vectors and identities, saved base/history, pool payloads and input.
5. Refactor live to singular full-pattern[1 2;2 4]. Expect SingularException;
   candidate uses symbolic reuse. Existing catch must set refactor_workspace
   to nothing. Before any next solve, compare snapshot base/history/prepared
   identities AND owned values; saved values unchanged. Do not demand disposable
   work/auxiliary/extraction scratch rollback. Pool entries/history must not retire
   on failure. One forward and one transpose on liveB4 and savedB1 (4calls).

Per side:1HHconstructor,1savedcopy,3replace_column!,2refactorattempts (one success,
one expected singular),12HHsolves (8FTRAN+4BTRAN). Total2constructors,2copies,
6updates,4refactors,24HHsolves. No other HH/component/public/workspace calls.
HH extraction may internally use at most one native scale-orientation solve per
successful construction/extraction: four extraction entries total, at most4such
native solves additional to the24HHsolves, with zero extraction for failed LU.
Do not count these implicit solves as zero; capture a source-bound upper bound,
not an observed backend-entry count unless a separate bounded amendment permits
instrumentation. Underlying6native numeric constructions total:2initial+2success+
2singularattempts. No warmup, extra controls, retries or copies.

## Oracles and controls

Default controls/q=nothing; no tolerances/precision/policy changes. Exact rational
oracles for the four2x2matrices and rhs[1,2] are computed offline and stored before
launch. FTRANupdate calls use their declared new-column RHS; final validity checks
use fixed residual64eps(Float64)*max(1,opnorm(B,Inf)*norm(x,Inf),norm(rhs,Inf)),
transpose likewise. Each solved matrix/RHS paired to its actual state, no production
certificate substitution. Record observed bits/equality, never require identical
reference/candidate trajectories or change bounds to rescue an outcome.

Two actual update directions must meet unchanged zero_tolerance for their pivot;
do not inject a direction or bypass a prepared-state check. The third uses B3 as
its prior basis. Initial/successful native backend symbolic identity captured with
old owner held; numeric IDs likewise. Failure must discard private backend without
publishing a new base or invalidating prior prepared values. Saved factor has
private solve/extraction scratch and no native construction workspace; shared
prefix records cannot be recycled/modified. Verify exact values and aliases,
not mutable-reference-only comparisons. No growing diagnostic native ledger.

Preforward bounded counters for declared constructor/copy/update/refactor/HHsolve
calls, including expected throws. No adapter or helper that fabricates numerical
results. Count scalar snapshots and comparisons separately; do not label diagnostic
copies as production overhead. No speed benchmark in this correctness gate.

## Launch and acceptance

Before changing new diagnostic sources and separately before launch, verify prior
runner3792/child3793/group3788 absent with boot/start/command and no Julia. Pin
actual source/test/runtime/environment/driver/clones/launcher/inputs, native wrapper
and resolved libraries; verify user hashes. One guarded process, Julia/BLAS1,
heap2GiB, VM8GiB, RAM>=6GiB, swap<=1GiB, wall600s. Forbiddenbig/largo/AnyMODaliases.
No source edits during run. Record loaded UMFPACK path/hash and ambient precision/
rounding/thread state. Stop on unexpected failure, preserve raw/source/exit and
unexecuted remainder; no automatic numerical retry or weakened predicates.

Postexit process/absence/exit, fresh independent full pin verification, actual
clone/source/GREEN binding, raw/portable equality and exact work/state audit.
Fresh independent numerical/work/memory review before any further separate plan.
No production promotion. Required later gaps: actual workspace borrowed assembly,
dimensions/empty/nonfinite basis policy, controls changes/invalidation, representative
cost and native retention; S4-F simple fallback is not full HH lifecycle proof.
Original-model certification, S2-A/S6-J/wholeAF rejection and CI-disabled state stay.
