# Allocation audit: MPS reader

This second round targets input parsing and model construction. The preceding
presolve changes remain in place. The baseline MPS code is unchanged from
`4fb2026`; measurements use Julia 1.13.0 on aarch64-linux-gnu with one Julia
thread. Each entry is the minimum of three warmed calls, with no compilation
observed in any measured call. These are cumulative Julia heap allocations,
not peak memory.

## Findings and changes

The full-allocation profile of `adlittle` identified temporary token strings,
fixed-field extraction, and eagerly formatted arithmetic-error messages as the
main avoidable costs.

- Numeric construction now formats diagnostics only when an arithmetic check
  fails. Checked arithmetic, source locations, and error text are preserved.
  This change alone reduced `adlittle` construction from 246,664 to 114,056 bytes.
- Header classification uses temporary substring views. Free-format records
  reuse those tokens instead of splitting the line again.
- Fixed-format extraction uses bounded views of the original ASCII record.
  Missing trailing columns still behave as blanks. Six temporary fields live
  in a tuple; only the returned field vector is allocated. No padded string is
  needed.
- Names stored in the accumulator and the resulting `LinearProblem` remain
  owned `String` values. Format detection, comments, continuations, supported
  numeric types, and named-set selection keep their existing semantics.

## Results

| Input / format | Before (B) | After (B) | Fewer bytes | Before allocations | After allocations |
|---|---:|---:|---:|---:|---:|
| afiro / auto | 166,328 | 102,952 | 38.1% | 2,657 | 1,179 |
| adlittle / auto | 680,528 | 405,184 | 40.5% | 10,894 | 4,504 |
| adlittle / fixed | 680,528 | 405,184 | 40.5% | 10,894 | 4,504 |
| kb2 / auto | 464,096 | 283,536 | 38.9% | 7,058 | 2,897 |
| sc50a / auto | 258,808 | 154,152 | 40.4% | 4,207 | 1,788 |
| flugpl / auto | 167,224 | 101,656 | 39.2% | 2,832 | 1,246 |
| greenbea / auto | 45,332,560 | 27,898,832 | 38.5% | 662,173 | 259,488 |
| basic-free / free | 20,048 | 14,448 | 27.9% | 363 | 258 |

Every stored `LinearProblem` field was compared with a serialized pre-change
snapshot using `isequal`, including sparse matrix data, names, domains, bounds,
objective coefficients and objective constant. All eight cases matched exactly.
The `greenbea` check covers loading, not a claim about its solve status.

Machine-readable phase measurements are in
[`mps-allocations-before.toml`](mps-allocations-before.toml) and
[`mps-allocations-after.toml`](mps-allocations-after.toml). The `parse` stage
includes file I/O and symbolic records; `build` operates on prepared records.
Timings were collected while other validation ran, so no runtime-speedup claim
is made. These savings affect `read_mps` and workflows that load files; calling
`solve` on an already constructed model does not include MPS parsing.

## Reproduction

Use the existing full-pipeline audit on the smaller registered datasets:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=read_mps --output=mps-audit.toml
```

To isolate loading and construction, including `greenbea`, run the following in
Julia with `--project=dev` from the repository root. This avoids running the
solver while investigating input allocations.

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

path = "dev/fixtures/greenbea.mps"
format = :auto
records = JSimplex._parse_mps_file(path; format)
measure_allocations(_ -> read_mps(path; format); samples=3)
measure_allocations(_ -> JSimplex._parse_mps_file(path; format); samples=3)
measure_allocations(_ -> JSimplex._build_mps(records); samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and input files for comparisons.

## Regression coverage

The new allocation tests were observed failing before the changes. They bound
both complete loading and symbolic parsing of `adlittle` in automatic and fixed
formats. Additional tests cover retained names, embedded dollar signs, trailing
comments and numeric values for Float32, Float64, BigFloat, Rational{Int}, and
Rational{BigInt}. Existing MPS tests exercise malformed input, exact arithmetic,
overflow diagnostics, fixed continuations, names containing spaces and format
detection.

An independent review compared fixed-field parsing against the original code
across record lengths 0–90, five sections and all three formats: **13,650
differential checks passed**, including error types/messages on malformed input.
The GLPK comparison suite passed all six numerical fixtures (`adlittle`,
`flugpl`, `kb2`, `markshare_4_0`, `sc50a`, `stein9inf`).
The allocation-audit development tests also passed all 27 checks after the MPS
changes.
The complete mandatory suite passed **14,187/14,187** tests, including the new
84 MPS allocation/name checks and the existing numerical type, solver, and MOI
regressions.
