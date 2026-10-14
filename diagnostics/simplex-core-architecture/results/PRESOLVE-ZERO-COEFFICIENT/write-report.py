from pathlib import Path
import json,statistics
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/PRESOLVE-ZERO-COEFFICIENT'
a=json.loads((D/'partial-analysis.json').read_text());v=a['records'];lines=[]
for n,r in v.items():
 b=r['reference'];c=r['candidate'];lines.append(f"| {n} | {b['bytes']:,.0f} → {c['bytes']:,.0f} | {b['events']:,.0f} → {c['events']:,.0f} | {r['median_paired_time_ratio']:.4f} | {'PASS' if r['bytes_nonincrease'] and r['events_nonincrease'] else 'FAIL'} |")
report='''# Sparse equality missing-zero conversion experiment

2026-10-14. Baseline master `6f68e24e8ddac42b948da8fcc2d636c010751194`;
diagnostic entry `65e524a6bf0a9cd4ea80c26cb36f26c6429954f0`.
Evidence: `results/PRESOLVE-ZERO-COEFFICIENT`.

## Decision

**Do not promote this candidate.** Its zero-conversion target works and all
5,155 focused assertions pass, but three controls show material increases in
allocation events and bytes. This violates the agreed no-allocation-increase gate.
No production, permanent test, environment, CI or master change. This is rejection
of this concrete sentinel implementation, not proof that zero-conversion removal
is impossible. No second candidate, tuning, retry, or further numerical run follows.

## Change and correctness

A separate ordinary source overlay changes only two fragments of
`src/presolve_aggregation.jl`. Only Float64 uses `get(matrix_updates,key,nothing)`;
on a dictionary miss it reads the original coefficient once. A stored zero with
nonzero exact multiplier leaves a `nothing` marker, which selects the existing
exact-product negation. Staged hits, zero multipliers and other precisions retain
exact values. The full original function is reconstructed by reversing the two
fragments. Reference aggregate/dispatcher/full-presolve copies have only scoped
renames, with unchanged helpers/types; no original method is overwritten.

The RED test ran before the candidate existed. Its forwarding counter records the
actual original missing-entry conversion, then calls the original exact converter.
The tiny model 2x+3y=4,4x<=20 reduces to coefficient -6 and upper12. Correctness and
source preservation passed; demanding zero conversions failed exactly 1==0:
2 PASS / 1 expected FAIL, exit1. This is a work test, not a solver defect or source-
text assertion. Separate candidate probe on four row pairs records reference4 /
candidate0, with complete result equality. Counters are diagnostic only and absent
from timed candidate/reference functions.

GREEN completed 5,155 assertions: 88 new signed-zero/staging/owner assertions,
5,064 existing assertions from five focused aggregation files, and three work-probe
checks. Existing coverage includes Float32/Float64/BigFloat/Rational{BigInt}, tiny
nonzero values, reduced ambient precision, unrepresentable fill, committed nonzero
updates and cancellation, exact outputs and postsolve. These are focused tests,
not full-suite acceptance or actual CI success. No numerical safeguard changed.

## Preserved failure and measured scope

The admitted GREEN process later failed BEFORE the first small Netlib call because
the new driver incorrectly passed `native_reader=true` to `read_mps`, whose native
API has no such keyword. This is a driver error. Tests and all nine synthetic cases
had already completed and were saved separately. No Netlib/full-presolve/large-model
candidate measurement occurred. The run stays exit1, final raw.toml absent; it is
NOT a complete qualification or PASS. The launcher then failed closed on missing
raw.toml; its error does not replace the preserved Julia error/process record.
`partial-analysis.json` independently reconciles only the saved subset and records
`complete_qualification=false`. Nothing was rerun to repair the incomplete record.
The existing synthetic cost failure already rejects this candidate, so correcting
the reader and continuing measurement would not justify production promotion.

Original RED admission was rejected for loose count/path audit predicates. Separate
`launch-reviewed.py` requires exactly one RED conversion and exact configured source
path. Initial GREEN preparation had a nonexistent afiro fixture path and did not
encode strict target allocation reduction; separate `green-reviewed.jl` corrected
both before execution. Original rejected reviews, source and manifests remain.
The unsupported reader keyword was missed by author and admission review and is
explicitly preserved here. `author-source-check.json` false fixture gate and its
separate correction are also preserved.

## Costs

Nine cases, three warm pairs and eight measured pairs each, alternating order:
99 pairs / 198 aggregate calls in this measured schedule, including 27 warm pairs.
This is not the total process call count: correctness tests and probes are additional.
Each measured call includes all aggregate setup, staging and result construction.
Fixture construction, explicit GC, deep input snapshots, full result comparison
and owner checks are outside the timed call. Both results remain live for comparison;
alternation bounds order imbalance but is not observer-neutrality or native-free
proof. All 72 measured pairs / 144 windows have zero compile/recompile counters.
All 99 saved pairs have identical complete results and unchanged input values/owners.

Table: median per-call cumulative GC-accounted bytes/events, median paired
candidate/reference elapsed ratio (includes in-window GC). All samples/ranges are
preserved. Bytes are not peak/live/retained native memory. Gate was fixed BEFORE
measurement: median bytes AND events must not increase on ANY case, with strict
reduction on all four signed sparse targets. No allocation-noise waiver.

| Case | Bytes reference → candidate | Events reference → candidate | Time ratio | Cost gate |
| --- | ---: | ---: | ---: | --- |
'''+ '\n'.join(lines)+'''

The four signed sparse targets remove 768 events for 128 independent updates,
i.e. six events/update, and about 1.5% bytes. Timing ranges overlap and two signed
case median ratios are slightly above1; there is no universal speedup or measured
full-presolve improvement. The explicit-negative-zero target has a lower local
median ratio but is not a large-model or general speedup claim.

Control regressions are event-count changes, not just byte noise: nonzero-old adds
512 events / 18,432 median bytes; zero-multiplier adds384 /14,352; populated dense4x4
adds36 /1,296. The source-level absence of new scratch/scans is insufficient to prove
allocation nonincrease. The sentinel changes inferred/control-flow representation;
these measurements do not identify a specific compiler boxing or allocation site.
No unsupported causal claim about the exact mechanism is made.

## Work, memory and boundaries

Affected frequency is each attempted sparse-equality matrix update, repeated across
presolver visits. The candidate retains one dictionary lookup and original CSC
lookup on misses, adds a stored-zero scalar check and sometimes an exact multiplier
zero check, and avoids an exact zero conversion on the intended path. It adds no
explicit scan, cache, scratch vector/matrix, solve, retained worklist or BigInt
mutation. Matrix dimension/nnz staging work and fill caps remain unchanged. Nevertheless
it introduces avoidable runtime allocation work on controls, so the production
work/memory review rejects it. No all-precision performance claim follows from
unchanged generic arithmetic or passing correctness tests.

Both processes obeyed Julia/BLAS1, existing compiled modules, heap2GiB hint, VM8GiB,
availableRAM6GiB and swap1GiB guards; each inclusive limit120s. RED launcher elapsed
6.9444s, GREEN Julia guard elapsed29.4534s (launcher inclusive timing is separately
recorded); these are not benchmark numbers. Fresh complete historical and new PGID
ORsession scans show no remaining Julia. Launch inventories and protected sources
were checked after execution; no old numerical driver/auditor was rerun.

The previous profile remains frozen. Its live STATUS/roadmap bindings must resolve
only to this experiment's `STATUS.md.before-zero`/`roadmap.md.before-zero` after
continuation changes; prior report-before mappings and all older mappings remain.
Broader optimization plan open; automation paused, CI off, HH reuse disabled.
'''
p=R/'diagnostics/simplex-core-architecture/PRESOLVE-ZERO-COEFFICIENT.md'
with p.open('x') as f:f.write(report)
