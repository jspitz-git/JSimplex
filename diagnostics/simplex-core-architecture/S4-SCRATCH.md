# S4-A: HH dimension-dependent scratch ownership

## Scope and observed failure

The old refactorization creates correctly sized extraction work/auxiliary arrays
on a dimension change, then discards them and resizes the old four private
solve/preparation arrays. Julia1.13 shrinking retains their backing Memory.
RED on a65536-row Float64/native diagonal, followed by4 and0 rows, observed
262144 backing elements after both changes, versus required16 and0. That is
2MiB of fixed-size scalar payload retained in these four arrays alone.

The candidate prepares all four references before publication, reuses extraction
arrays on a changed dimension, and preserves same-size identity. New prepared
arrays are undefined until the existing complete initialization before
prepared_valid=true. The old dimension still controls update pool retirement.
No numerical arithmetic, factor extraction, tolerance, precision or symbolic
reuse policy changes. Existing saved factors remain independent and may
legitimately retain their own storage.

## Verification so far

- red-1: exit1, unchanged pins,6 passes/2 intended backing-capacity failures.
- green-1: normal compilation, exit0, unchanged pins,344 assertions passed.
  Both backends, Float16/32/64, BigFloat, Rational{Int/BigInt}, growth/shrink/empty,
  forward/transpose solves, same-size identity, saved copies and failed candidate
  preservation are covered.
- focused-1: normal compilation, exit0/pins unchanged,4366 assertions passed
  (including the344 new regression assertions). Factor/update history, precision,
  native/Markowitz, public solves, MOI and precision transfer are covered.
- cost-1: exit0/pins unchanged,60 records; all factor, forward and transpose
  fingerprints match, all measured compilation and GC are zero. Three interleaved
  pairs per case after separate warmup. Integrated-master regression passed.

All numerical jobs use the common serial/resource guard. Raw logs, scripts,
source snapshots, pins and process/resource reports are preserved under
.superpowers/simplex-core-architecture/S4-A/. Portable evidence follows completion.

## Work and memory review

Independent static review found no blocker or unnecessary new work/retention.
The affected frequency is refactorization, not each iteration or candidate.
Two small prepared-array allocations are added on shrink; work/auxiliary
allocations already existed and now remain owned rather than being discarded.
No new vector scan, matrix traversal, basis solve or copy is introduced.
Same-size vector identity is tested and measured allocation cost is unchanged.

The failure contract preserves base/history/prepared identity and data if
candidate construction/extraction/vector preparation fails. Existing later
pool/unit-workspace allocation failures are not claimed fully transactional.
This change bounds only these four private vector backing capacities; it is
not a bound on live factors, saved checkpoints, backend storage, arbitrary-
precision scalar payload or process allocator/JIT memory. Timing claims must
remain separate from retained-capacity evidence.

## Measured refactorization cost and retained capacity

Eight same-size refactors per sample, Float64, three paired samples per case:

| Backend / matrix | Baseline/candidate median ms | Baseline range ms | Candidate range ms | Bytes / events, both sides |
| --- | --- | --- | --- | --- |
| Native sparse512 | 1.7767 / 1.2917 | 1.2585–2.3703 | 1.2465–1.2997 | 4784544 / 920 |
| Native dense96 | 2.2363 / 2.2284 | 2.2240–2.5238 | 2.0698–2.2601 | 10099024 / 896 |
| Markowitz sparse512 | 0.8788 / 0.8550 | 0.8498–0.9629 | 0.8361–0.8564 | 1988496 / 5013 |
| Markowitz dense96 | 0.9655 / 0.9835 | 0.9517–1.0782 | 0.9411–1.0249 | 7578392 / 1059 |

Sparse/native bytes vary by48B in both sides; the table reports medians.
Same-size allocation counts and paired bytes are unchanged. Overlapping ranges
and the small sample count do not establish a speedup. Markowitz/dense's+1.86%
median difference is within the observed overlapping spread; no material cost
regression is demonstrated, and static review finds no new size-dependent work.

Changed dimensions follow native65536 or Markowitz2048 ->4 ->0 ->7. Baseline
retains262144 or8192 Float64 backing elements throughout. Candidate retains
16,0,28 elements, namely128,0,224B. Each transition's factor and forward/transpose
hashes matches its baseline. New prepared arrays cost+192B/+4 allocation events
at n=4,+64B/+2 at n=0,+224B/+4 at n=7; two nonempty Julia vectors involve both
headers and Memory allocations. This bounded cost releases obsolete capacity.
Native n=7 time has a higher candidate median73.0us versus58.8us with broad
51.8–87.5us /51.8–65.2us ranges; no changed-dimension speedup is claimed.

No production source changed between GREEN, focused suite and cost measurement;
all508 active src/test hashes match their three pin manifests. Raw process
resource samples and compact peak summaries remain separate from array-capacity
metrics. Full suite/whole-medium performance and broad S4 backend attribution
are not established by this bounded lifecycle fix.

## Acceptance and integration

Independent final review accepts the local fix, with no remaining blocker and
no unnecessary work or memory finding. Reviewer recomputed all60 records and
30 paired fingerprints and checked the same production hash in three gates.
Architecture production commit8701a58; master cherry-pick4143dad.
integration-1 passed344 assertions directly on master, exit0/pins unchanged.
Host verified runner268317/child268318 absent, and main user-file hashes match
the pre-integration snapshot. Master4143dad27581cf1230fa74203306f956b89109a6
was pushed and verified with git ls-remote. Diagnostics remain
separate on the architecture branch, and local environments/user dirt are kept.
