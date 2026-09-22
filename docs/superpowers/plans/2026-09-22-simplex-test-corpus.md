# Simplex Test Corpus Implementation Plan

> **For agentic workers:** This document refines F01 and the validation steps of F03–F25 in the [main plan](2026-09-22-simplex-modernization.md). It does not start solver implementation.

**Goal:** Evaluate the algorithms on the user's local collections while keeping oversized models in a separate, bounded stress suite.

**Architecture:** Discover inputs by collection and path, stream compressed inputs, and record reproducible case identities. Keep solve benchmarks and stress probes as distinct execution modes with enforced budgets.

**Tech Stack:** Julia 1.13, existing MPS reader, development benchmark runner, SHA-256, and external gzip decompression without new production dependencies.

**Spec:** [Modernization specification](../specs/2026-09-22-simplex-modernization-design.md).

## Global Constraints

- Julia 1.13; preserve support for Float32, Float64, BigFloat, and rational types.
- Production dependencies remain LinearAlgebra, Logging, MathOptInterface, OrderedCollections, and SparseArrays; this plan adds no dependencies.
- Work in .worktrees/simplex-modernization on branch feature/simplex-modernization, starting from commit d93cfd3.
- Each verified feature gets its own commit, including tests, documentation, and a validation report.
- Preserve Solution{T}, existing statuses, explicit LP relaxation, and validation against the original model.
- Share the time limit and completed-step budget across phases, repairs, retries, algorithm switches, and precision increases.
- Do not weaken user tolerances or certification to make a benchmark pass.
- Exact rational arithmetic uses neither floating-point perturbations nor automatic conversion to floating-point arithmetic.
- Working perturbations must not modify the input model and must be removed before certification.
- Algorithm changes need not preserve bitwise intermediate results or the pivot path.
- Write all material intended for the remote repository in English, including documentation, code comments, reports, and commit messages.
- Use /home/jspitz/NetLib, /home/jspitz/MIPLib, and /home/jspitz/mps as the external test collections; solve MIPLib cases only as explicit LP relaxations.
- Exclude big.mps, largo.mps, and AnyMod.mps (stored locally as AnyMOD.mps) from complete simplex solves; use them only for explicitly bounded stress tests.

## Review Focus

- MIP optimum metadata is not an LP-relaxation reference.
- Compressed and uncompressed copies must not leak between calibration and holdout.
- Explicit file selection and case changes must not bypass oversized-model exclusions.
- A truncated stream or an extracted subproblem is not the original complete LP.
- Resource-limit outcomes must be visible without contaminating solve-speed scores.

## Observed inventory

Read-only filesystem inspection on 2026-09-22 found:

| Collection | Local root | Observed MPS inputs |
| --- | --- | --- |
| NetLib | /home/jspitz/NetLib | 94 .mps files |
| MIPLib | /home/jspitz/MIPLib | 1,065 .mps.gz files |
| Additional models | /home/jspitz/mps | 10 .mps files |

Ignore collection ZIP files and solver logs during case discovery.
Inventory counts describe this inspection and may change; F01 must rediscover
and record the actual inputs used for a run.

The additional directory contains cba.mps, runtime.mps, aaa.mps, fast0507.mps,
nw04.mps, medium.mps, test.mps, largo.mps, AnyMOD.mps, and big.mps.
The user's AnyMod.mps refers to the locally observed AnyMOD.mps. Resolve the
actual file and apply the exclusion case-insensitively.

| Stress-only file | Observed bytes | Permitted evaluation |
| --- | ---: | --- |
| /home/jspitz/mps/big.mps | 1,701,545,686 | Bounded parsing, memory, and component probes |
| /home/jspitz/mps/largo.mps | 142,643,690 | Bounded parsing, memory, and component probes |
| /home/jspitz/mps/AnyMOD.mps | 486,154,800 | Bounded parsing, memory, and component probes |

The exclusion is the user's explicit constraint, not a size heuristic:
largo remains excluded even if another eligible file has a similar size.

## Solve suites

Keep the existing checked-in fixtures as fast, network-independent regression
tests. Use the following external cases in the development benchmark runner:

| Suite | Initial selection and purpose |
| --- | --- |
| quick | NetLib afiro, adlittle, kb2, sc50a; MIPLib pk1, flugpl, stein9inf, markshare_4_0, all as LP relaxations where applicable |
| degenerate | NetLib degen2/degen3 and MIPLib pk1/markshare_4_0, plus deterministically selected eligible cases and generated regressions |
| ill_conditioned | Local runtime.mps and numerically difficult cases identified by measured residuals/failures; do not infer conditioning from a filename alone |
| phase_one | Eligible NetLib/MIPLib models requiring feasibility restoration, including LP-feasible integer-infeasible examples; record phase costs separately |
| sparse_large | NetLib greenbea/pilot87 and eligible local medium, cba, aaa, fast0507, nw04, test; admit further MIPLib cases after resource screening |
| holdout | Freeze a disjoint sample of eligible cases before tuning; stratify by collection and available dimensions/nonzeros, with content-based deduplication |
| stress | Only bounded probes, explicitly enabled; includes big, largo, and AnyMOD |

Some calibration suites may overlap; report aggregate performance once per
unique case/configuration, rather than counting the same LP several times.
Exclude holdout content from every tuning suite and freeze its manifest.
Screening is not an instruction to solve all 1,065 MIPLib cases without limits.
Record screened-out cases and the reason; do not silently remove hard cases.

For each case record collection, relative path, actual spelling, compression,
source SHA-256 when fully read, decompressed SHA-256 when fully processed, dimensions/nonzeros
when known, LP-relaxation flag, reference provenance, and selected budgets.
For a bounded partial read, record the full-file hash as unavailable and label
any prefix hash with its byte range. Do not report it as a complete-file hash.
References must describe
the same stored model and its LP relaxation. Use existing GLPK comparison
support and exact small-case oracles; do not assume every corpus has a trusted
LP reference objective.

## Compression and read-only inputs

- [x] F01 discovers .mps and .mps.gz under the three configurable roots and rejects missing/ambiguous selections with a clear report.
- [x] Decompress .gz through a bounded stream or a disposable file in a task-specific temporary directory. Use an argument-vector subprocess invocation, not shell interpolation of filenames; use the available gzip executable or an already-supported development mechanism.
- [x] Enforce time, decompressed-byte, and temporary-disk budgets. Do not overwrite or decompress next to the source. Clean task-owned temporary files after success, failure, or cancellation.
- [x] Test a tiny gzip fixture against the same uncompressed LP, a corrupt/truncated stream, a path containing spaces, an exceeded decompression quota, and early cancellation.
- [x] Explicitly set relax_integrality=true for MIPLib solve comparisons and record that choice. A MIP-infeasible label does not certify LP infeasibility.

Implement a configurable default decompression quota of 2 GiB per input.
Exceeding it is a recorded input/resource limit, not NUMERICAL_ERROR or a
mathematical LP status. Metadata and error records remain available if parsing
does not finish.

## Oversized-model stress protocol

The names big.mps, largo.mps, and anymod.mps are stress-only after
case-insensitive normalization and removal of an optional .gz suffix.
Apply the rule to canonical paths and aliases before launching work.
Known duplicate content inherits the classification. Explicit --file
selection does not authorize a full solve or override this rule.

Default bounded probes:

- Streaming inspection: at most 256 MiB of decompressed input and 60 seconds; report a partial inspection if the budget ends.
- Full-reader stress attempt: opt-in, 300 seconds and a 4 GiB process-memory budget, reduced if local capacity is lower. A controlled resource stop is a valid stress outcome, not a successful complete parse.
- Matrix/vector/component probes: only after guarded loading or from an explicitly extracted, tractable subproblem; at most 60 seconds, 256 rows/columns for basis work, and 50,000 nonzeros in the extracted block.
- No full-sized basis construction/refactorization, unrestricted presolve, or complete simplex solve on these three models. Never pass an arbitrary byte prefix to the solver as a valid complete model.

The runner uses a separate process for a stress probe, an external watchdog,
and an available OS memory limit; if it cannot enforce the required limits,
it skips the probe with an explicit reason. A solver-internal deadline alone
does not bound parsing or a long native allocation.

Extracted subproblems record the extraction recipe and have separate case IDs.
Their correctness or speed says nothing about solving the full source model.
Stress reports distinguish completed parse, partial inspection, resource stop,
reader error, and component outcome; they do not enter solved-instance counts,
performance profiles, or the default-rollout speed score.

## Required F01/F25 selection tests

- [x] --suite=quick and every ordinary solve suite exclude all three stress-only files.
- [x] --file=/home/jspitz/mps/big.mps in solve mode is rejected before parsing or factorization.
- [x] AnyMod.mps, AnyMOD.mps, a resolved symlink, and an optional compressed form receive the same stress classification.
- [x] --suite=stress requires --mode=stress and explicit budgets; it cannot silently fall through to solve.
- [x] Eligible runtime.mps, medium.mps, and NetLib/MIPLib selections remain available for bounded complete solves.
- [x] Stress resource stops and missing corpora remain in reports, without being counted as failed mathematical certificates or successful LP solves.

## Planned runner commands

These commands are implemented in F01. The three local roots are defaults
and can be overridden. Eligible large local solves explicitly request the
24 GiB WSL allowance; the worker clips it to OS-reported total memory.
For full runtime.mps comparisons, allow at least five minutes of solver time;
the F07 comparison uses 360 seconds. Earlier shorter runs are screening data.

~~~bash
julia --project=dev dev/simplex_benchmarks.jl --source=. --suite=quick --algorithm=both --samples=7 --time-limit=60 --iteration-limit=100000 --output=/tmp/simplex-quick.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/MIPLib/pk1.mps.gz --algorithm=both --samples=7 --time-limit=60 --iteration-limit=100000 --output=/tmp/simplex-pk1.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/mps/runtime.mps --algorithm=both --samples=3 --time-limit=1800 --iteration-limit=1000000 --memory-limit-mib=24576 --output=/tmp/simplex-runtime.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/mps/medium.mps --algorithm=both --samples=3 --time-limit=1800 --iteration-limit=1000000 --memory-limit-mib=24576 --output=/tmp/simplex-medium.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --suite=stress --mode=stress --time-limit=60 --memory-limit-mib=4096 --read-limit-mib=256 --output=/tmp/simplex-stress.toml
~~~

An explicit --time-limit always caps the selected stress operation, even when
the operation's default cap is larger. The example stress command performs
bounded inspections/component probes; full-reader attempts require the
separately implemented --stress-operation=reader option and their own budget.

## Validation performed for this plan revision

Inspected the three directory inventories, file sizes, selected-case
existence, and the first few decompressed lines of pk1, flugpl, stein9inf,
and markshare_4_0. No full solve or full read of the three oversized models
was started. Full algorithm evaluation belongs to F01 and later features.

## F01 implementation verification

All selection, compression, cancellation, reader-budget, and stress-mode checks
passed in the final 606-assertion development suite. Actual inspections read
256 MiB prefixes of big/AnyMOD and the complete 142,643,690-byte largo stream,
without parsing or simplex work. Large eligible baseline comparisons and the
corrected 24 GiB medium runs are recorded in the
[F01 report](../../../diagnostics/simplex-modernization/F01.md).
