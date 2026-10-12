# S4-G: diagnostic HH symbolic publication and saved-state qualification

New qualification on architecture HEAD ad3d010, production/test/CI identical to
master0eb75c3. One guarded process ran exactly the two reviewed Float64/Int64 native
HH lifecycles. All79runtime assertions pass, exit0;26audit gates,653pins,10separate
author supplement checks pass. Fresh external review is recorded separately.
This qualifies the narrow diagnostic candidate, not production symbolic reuse.

## Source and call boundaries

The reference calls actual production HH refactorize!. The candidate defines
three distinct routing names inside JSimplex from an exact source slice; no
existing method is overwritten. The only non-routing change is the Float64 lu!
reuse_symbolic keyword using the actual _same_umfpack_pattern on converted CSC.
The repeated conversion is identity for these same-typed CSC inputs. Offline
inverse-source equality, current/frozen clone bytes and runtime SHA bind this
claim. Native control values match the stored S4-F defaults, including IRSTEP0;
q remains the default. No production/tolerance/precision/safeguard edit.

Preforward declared entry counts, including both expected exceptions:
2actual HH constructors,2actual saved copies,6replace_column! calls,
4refactor attempts and24HH solves(16FTRAN,8BTRAN). The six native numeric entries
(2initial+2successful+2singular) are source-derived, not separately instrumented.
Four successful extraction entries can perform up to4additional native solves
for scaling-orientation validation; actual count is not captured. Update internals
also perform their existing unit-transpose transformations and packing. The24
count is the declared HH solve entry boundary, not all internal arithmetic.

Both sides independently start B0=[4 1;1 3]. Real prepared updates form
B1=[5 1;1 3], then B2=[6 1;1 3], with one saved B1 copy sharing the first immutable
update. A planned B2 forward solve establishes prepared_valid=true before
successful B3=[7 1;1 3] refactor; immediately afterward it is false. Later real
update forms B4=[8 1;1 3], and current-column2 FTRAN prepares valid values before
the full-pattern singular target[1 2;2 4]. No manufactured directions or retry.

## Observed publication and ownership

Success replaces the live extracted base and empties live history. Only the
private second update is retired into the live pools; the shared first update
retains its identities/values and is not recycled. Saved factors share base and
immutable history, while their solve/prepared/extraction/unit/pool storage is
private and their native refactor workspace is absent. Caller B3 colptr,rowval
and nzval are then overwritten; extracted factors and private native CSC remain
usable and independently owned. The successful candidate retains symbolic owner
identity; reference rebuilds it. Both replace numeric owner identity. Prior owners
are held while comparing identity, so recycled addresses cannot establish reuse.

Both singular attempts throw SingularException with native status1, discard the
live refactor_workspace and leave extracted base, history, pool contents,
prepared direction/partial, saved state, and their recorded identities/owned
values unchanged. Candidate symbolic identity remains the same; numeric identity
changes. Live B4 and saved B1 forward/transpose solves subsequently pass. This is
not rollback of the mutated failed native backend, which is observed only through
a diagnostic held reference and not republished. Failure occurs in LU before
extraction; it does not qualify later allocation/extraction failure rollback.

All24new solve outputs satisfy the fixed64eps scaled residual bound. Offline
Python rational reconstruction from matrix/RHS/output bits independently matches
all24exact residual records and verifies the same exact bound; exact residuals
need not be zero. Five basis oracles were stored before launch. Every call is
matched to its actual prior matrix, including update and pre-refactor calls.
Reference/candidate endpoint bit equality is not an acceptance requirement.

## Work, resources and evidence limits

No production work or memory changes. The diagnostic keeps bounded2x2state,
16serialized owned state snapshots(two sides × eight),24solve records and small
identity owners, plus transient comparisons and copies. There are no per-iteration
production ledgers, extra numerical control calls, warmup, metadata extraction
calls outside the existing HH implementation, graph scans or benchmark runs.
These records are diagnostic overhead; no speedup or allocation/native-retention
bound is claimed. Held previous native owners can delay reclamation in this run.
Source-bound upper counts are explicitly separate from observed entry counters.

Julia/BLAS1,heap2GiB,VM8GiB;five resource samples, minimum available RAM22863924KiB,
maximum swap0. Runner5238/start202699/group5234 and child5239/start202780/group5239
are absent on bootdade7243-9103-4398-bb45-fa28fbc0be72; full/proc group scans were
empty. User hashes preserved. Loaded UMFPACK path/hash was checked;13resolved
native files are pinned, not a capture of every loader choice. Raw report SHA:
123ded27edbc0ea6cc50a00abbb5186ad1e86e1633af688e5627e662572b25c5.

Evidence: results/S4-G/publication-1-{report.toml,process.json,pins.json,audit.json},
clone-source.json,exact-inputs.json,independent.json,host-after-publication-1.json.
Raw/frozen sources remain under .superpowers/simplex-core-architecture/S4-G.
No accepted driver/auditor/supplement rerun. Original reviewed plan is pinned and
must not be edited retroactively. No public simplex/workspace integration,
nonfinite/empty/dimension/control-change policy, representative cost/native-memory,
fullsuite/x64/CI-cause or production enablement claim. Existing rejections stand.
