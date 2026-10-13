# Markowitz construction workspace retention qualification (S4-AA)

One authorized guarded attempt completed on 2026-10-13: exact S4-Y canonical
driver through the frozen S4-Z launcher, qualification-1. All66 named predicates
passed (33 sparse,33 dense), process and launcher exit0, all6 admitted audit gates
PASS and all8 supplementary postchecks PASS. No retry or changed numerical input.
This qualifies the scoped diagnostic, not a retention optimization or solver defect.
Production/test/environment/CI/master remain unchanged; automation remains paused.

## Observed reachable graphs and retained structure

Both cases use Float64 direct Markowitz backends128→8→8→128. The construction
workspace has128 row dictionaries,128 column dictionaries,128 maxima and128
valid flags at every captured stage, with original container owners preserved.
Each snapshot records13 row entries and13 column entries. Sparse small resets
have active row/column lengths8; dense small bypasses retain those lengths128.
Each of the eight workspace reachable graphs measures94888 bytes.

| Case | Stage/dimension | Active rows/columns | Workspace graph B | Backend graph B | Spare dimension | Dense core rows |
| --- | --- | --- | --- | --- | --- | --- |
| sparse | 1/128 | 128/128 | 94888 | 135752 | absent | 5 |
| sparse | 2/8 | 8/8 | 94888 | 96832 | absent | 5 |
| sparse | 3/8 | 8/8 | 94888 | 98760 | 8 | 5 |
| sparse | 4/128 | 128/128 | 94888 | 137808 | 8 | 5 |
| dense | 1/128 | 128/128 | 94888 | 135752 | absent | 5 |
| dense | 2/8 | 128/128 | 94888 | 96256 | absent | 8 |
| dense | 3/8 | 128/128 | 94888 | 97592 | 8 | 8 |
| dense | 4/128 | 128/128 | 94888 | 137112 | 8 | 5 |

These graph estimates overlap; do not add workspace and backend sizes. They are
not native allocation/free balance, bytes returned to the OS, peak memory or a
GC collection measurement. Saved factors and original owner references remain
live. There is no fresh-small control, retained-capacity trimming comparison or
allocation/time comparison. Equal graph sizes here do not prove all future
shrink histories have a constant cost or constitute a leak.

The saved backend copy has no construction workspace/spare; its two original
matrix solves still pass after the live chain. Source `_copy_backend` marks the
original shared, and `_refactorize_backend` only adopts a private old backend as
spare. Thus the absent stage2 spare is consistent with the saved-copy ownership
path; stages3/4 record spare dimension8. This is source interpretation of the
captured metadata, not a full alias graph or failure-lifecycle qualification.
Both factor pools are recorded empty at all eight stages.

All20 solution predicates passed the unchanged componentwise absolute
64*eps(Float64) bound against ones; input matrices remained equal to their copies.
The source schedule is2constructors2copies6refactors20backend solves, eight
snapshots and66predicates. It was not instrumented with PREforward method counters;
internal numerical/import work is additional. Ten helpers produce50 explicit
vectors, plus four input copies, sixteen dictionary-length scans, sixteen graph
walks and input comparisons. No unnecessary production work or memory is added.
Existing64→3→64 allocation-free regrowth/maxima-owner and512graph contracts remain.
No universal current-dimension cap or threshold chosen around test sizes is admitted.

## Admission, resources and provenance

Fresh independent gpt-6-astra numerical admission accepted the711-entry launch
manifest SHA a76a46350a87ededd788c8615b7570f78716e970e5900d037b89c57661f05efd,
all698 required bindings,69 Z final bindings and27 committed Z blobs.
Exact driver SHA476c5ea1556b4f8b8c35291f07527cf55579e9c920fe4c9537593dab87f46f6a.
The allowance explicitly binds the human permission, manifest and numerical review.
The user also authorized future short attempts without repeated permission; each
still requires its own concrete admission and caps. No multi-hour run is allowed.
That standing preference does not rerun a consumed reservation or reopen stopped
routes. Old instructions requesting repeated human permission are superseded by
this later human instruction; frozen historical texts are preserved unchanged.

One owned runner156956/start_ticks7624463/PGID156956 and child156957/start_ticks7624512/
PGID156957, bootdade7243-9103-4398-bb45-fa28fbc0be72. Four resource samples,
minimum available22089432KiB, maximum used swap0, terminal available22403792KiB.
Elapsed including launch4.005497608988662seconds is not a benchmark. The configured
120second/VM8GiB/heap2GiB/RAMfloor6GiB/swapmax1GiB/Julia-BLAS1 guards remained satisfied.
Full prior28 plus both new groups AND sessions were separately absent after exit;
no Julia remained. Actual command, current/terminal identities, reservation,
invocation, launcherlog, raw and resource records are retained.

Ordinary existing-only compiled-module loading uses the unchanged active project;
the source-path check completed. Exact source/environment/runtime file pins stayed
unchanged. This does not prove all runtime loader choices, cache confinement,
zero import work or compile-free measurement. No benchmark claim is made.

Original output remains at `.superpowers/simplex-core-architecture/S4-Z/qualification-1`;
all six files are byte-identical in results/S4-AA/qualification-1. Z receives only
new launch-pins/numerical-review/allowance/reservation/log/invocation/audit records;
its original scripts and evidence are frozen. `postcheck.py` is supplementary
post-exit analysis, NOT a launch pin. No historical auditor or numeric run repeated.

Z final STATUS/roadmap bindings resolve ONLY to AA before-S4-AA copies. Z/Y initial
maps and all older G/F/E mappings remain unchanged. Broad S2/S3/S4/S5/S6 remain open;
HH reuse stays disabled, CI stays off, S2-E consumed, S3-G route stopped and S6-AQ
still needs genuinely new original evidence. This one qualification is complete;
future policy work needs its own concrete source/design and cost/correctness gates.
