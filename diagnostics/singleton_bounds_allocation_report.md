# Lazy singleton column-bound copies

Round 23 delays the working bound copies in `reduce_singleton_rows`. Lower and
upper column bounds initially reference the input. Each side is copied separately
immediately before its first actual tightening. Later tightenings reuse that
private vector. Result construction still copies both sides, including a side
that never required a working copy.

Candidate arithmetic, exactness checks, bound sources, contradictions, row
selection, and restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 22 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped verification; no runtime-speedup claim is made. These are bytes
allocated per call, not peak or retained memory.

The dense 128 × 128 probe with no singleton rows fell from **12,232 to 7,992 bytes
(34.66%)**, and from 21 to 15 allocations. The identity-matrix probe tightens both
bounds on all 128 variables and still needs both copies: its allocation count
remained 12,852. Its byte total varied from 482,712 to 481,384; no saving is
attributed to this change for that path.

| Model | Singleton pass before | After | Reduction | Full presolve before | After | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| afiro | 16,800 | 16,224 | 3.43% | 1,176,104 | 1,171,768 | 0.37% |
| adlittle | 43,192 | 41,528 | 3.85% | 4,875,352 | 4,868,664 | 0.14% |
| kb2 | 4,480 | 2,944 | 34.29% | 13,169,520 | 13,162,336 | 0.05% |
| sc50a | 5,200 | 3,504 | 32.62% | 4,305,472 | 4,298,144 | 0.17% |
| flugpl | 11,864 | 11,864 | unchanged | 1,506,272 | 1,502,016 | 0.28% |

The direct flugpl pass still requires both copies; later singleton passes within
full presolve can avoid them. Whole solves with presolve enabled allocated
0.03–0.30% fewer bytes. The unchanged paths without presolve varied by -416 to
+32 bytes with identical allocation counts; that variation is not attributed
to this change. Isolated pass measurements give the clearest evidence.

All ten model snapshots (five fixtures × singleton/full presolve) matched exactly:
CSC arrays, objective and constant, sense, bounds, domains, names, and original
column count. All 20 whole-solve combinations remained `OPTIMAL`, with identical
status, objective, complete primal vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-bounds-allocations-before.toml`](singleton-bounds-allocations-before.toml)
and [`singleton-bounds-allocations-after.toml`](singleton-bounds-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_singleton_rows --output=singleton-bounds-audit.toml
```

The synthetic probes use the same inputs and commands as the preceding
[singleton scan report](singleton_scan_allocation_report.md).

## Regression coverage

The new budget failed before the change at 12,232 bytes against a 9,000-byte
limit and now passes at 7,992 bytes. The 73 new checks cover repeated lower-only
and upper-only tightening, the last tightening's source row, independence of both
result bound arrays, and unchanged source bounds after result mutation, across
Float32, Float64, BigFloat, and Rational{BigInt}. Existing singleton tests cover
both-sided changes, rejection, contradictions, and restoration.

Independent review found no issue. Its 180 differential cases across six numeric
types, including 37 contradictions, unbounded bounds, and rejected candidates,
matched baseline models, failure metadata, and bound-source maps without
modifying source bounds.

The complete mandatory suite passed **16,391/16,391** tests, including the 73 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
