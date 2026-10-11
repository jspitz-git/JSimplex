# S4-B: native HH component attribution

Status: diagnostic accepted; no production change. Source: architecture b6d32ca,
production identical to master b720674. Protocol:
[component subplan](../../docs/superpowers/plans/2026-10-12-hh-component-attribution.md).

## Method and acceptance

Four deterministic CSC fixtures (sparse/dense, dimensions 64/256), three separate
regions, six rotating rounds, 16 calls per sample. All 72 samples have zero measured
compilation. Backend, extraction and whole-refactor scopes have different retained
objects; their independent elapsed times must not be added. Constructors, explicit
pre-sample GC, fingerprints, residual checks and serialization are outside timing.

Attempt native-components-1 failed after 18 records because a report dictionary
inferred integer values before a case label was inserted. It remains preserved.
Changing only that dictionary to Dict{String,Any} allowed native-components-2 to
finish: exit 0, unchanged pins independently verified, all 13 post-exit gates pass.
Process identities were separately absent before any further source edits.

## Observed component costs

Each cell gives the median over six samples. Bytes and events are cumulative
allocation traffic per 16-call sample, not live-factor size. Full ranges, compilation
and GC are retained in results/S4-B/native-components-2-audit.json and reference TOML.

| Fixture | Region | Median ms / 16 calls | Allocated bytes | Allocation events | GC ms |
| --- | --- | ---: | ---: | ---: | ---: |
| dense-256 | backend | 21.754001 | 8.4614e+07 | 999 | 0.185350 |
| dense-256 | extraction | 4.121350 | 2.14171e+07 | 848 | 0.000000 |
| dense-256 | whole_refactor | 23.352301 | 1.06031e+08 | 1865 | 0.405050 |
| dense-64 | backend | 1.342351 | 6.46006e+06 | 976 | 0.000000 |
| dense-64 | extraction | 0.353900 | 1.4345e+06 | 688 | 0.000000 |
| dense-64 | whole_refactor | 1.764300 | 7.89379e+06 | 1664 | 0.000000 |
| sparse-256 | backend | 1.102900 | 4.30139e+06 | 960 | 0.000000 |
| sparse-256 | extraction | 0.251450 | 690944 | 832 | 0.000000 |
| sparse-256 | whole_refactor | 1.365100 | 4.99243e+06 | 1792 | 0.000000 |
| sparse-64 | backend | 0.364450 | 1.27218e+06 | 960 | 0.000000 |
| sparse-64 | extraction | 0.071350 | 185856 | 608 | 0.000000 |
| sparse-64 | whole_refactor | 0.497200 | 1.45814e+06 | 1568 | 0.000000 |

Backend traffic exceeds extraction traffic in all four fixtures. The fresh native
symbolic/numeric path is therefore a better next attribution target than assuming
extraction dominates. This does not identify avoidable allocations or demonstrate
an optimization. In particular, subtracting GC does not measure arithmetic time.

## Ownership, failure and retention

FTRAN/BTRAN residuals, saved-base fingerprints, same-size pattern changes,
256→64→256 dimensions and a singular-refactor failure pass. Saved checkpoints
continue solving their original basis. Failed refactorization drops private backend
state while preserving the live and saved immutable bases. Published value buffers
do not alias extraction scratch. Current code still disables HH symbolic reuse.

The deduplicated live-plus-fresh-checkpoint Julia graph is 23,248 / 186,104 /
82,368 / 2,784,024 bytes for sparse64 / dense64 / sparse256 / dense256. A fresh
checkpoint shares the current immutable base; its whole size must not be added to
the live size. Lifecycle graph rows measure this same pair and exclude the older
checkpoint retained by the lifecycle test. The shrink row is consequently not the
total retained memory of that lifecycle. Graph sizes exclude external UMFPACK
storage and hidden backing capacity. These records are not an RSS accounting.

Guard sampled RSS at most 464,128 KiB and VmPeak 1,052,420 KiB; minimum available
22,474,652 KiB, swap 0. Six guard samples do not attribute native memory to regions.

## Independent review and next gate

Fresh gpt-6-astra read-only review independently checked all 573 pinned files,
manifest digest, all sample identities and compilation, preserved failure and
lifecycle assertions. No blocking finding. It found no unnecessary production
work or retained-memory increase: this chunk changes diagnostics only. Diagnostic
scans/copies/forced GC serve validation and isolation outside measured scopes.
Direct ownership assertions cover work-vector independence and value-buffer
nonaliasing; source inspection confirms remaining scratch/index ownership. This
is not exhaustive coverage of every precision or backend.

Next: add analogous Markowitz component attribution in a separate script/attempt
with its backend-specific semantics and identical small fixtures, preserving this
accepted native reference. Then choose one measured production hypothesis and
write its ownership/failure/invalidation subplan. Native same-pattern symbolic
reuse is only a hypothesis: the existing PFI pattern helper costs O(n + nnz),
and UMFPACK symbolic construction also receives numeric values. Changed numeric
values, ordering, patterns and failed construction need qualification; same shape
alone never authorizes reuse. No tolerance, numerical policy or production code
was changed. No full-medium speedup or entire-S4 completion is claimed.
