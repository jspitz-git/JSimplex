# Optional row and column presolve

These passes are independently enabled with `SolverOptions` or the same MOI raw
optimizer attribute names. All three default to `false`:

```julia
options = SolverOptions(Float64;
    presolve_row_sparsification=true,
    presolve_column_merging=true,
    presolve_column_dominance=true)
solution = solve(problem; options)
```

`presolve=false` bypasses them. Float32, Float64 and BigFloat are supported,
including models whose stored BigFloat values have different precisions. Enabling
an optional pass with unsupported scalar arithmetic raises `ArgumentError`.
Options survive precision conversion, phase/recovery options and MOI copies.

## Reductions and recovery

The unchanged base presolve runs first, followed by one requested row batch,
one merging batch and one specialized dominance batch, in that order. Ordinary
presolve then consumes newly exposed MIN reductions. MAX retains its existing
base postsolve maps without this extra tail, which requires MIN dual history.

* Row sparsification adds a scaled equality to another row only when it removes
  nonzeros, respects the coefficient-growth bound and exactly represents the
  transformed coefficients and row bounds in the working type. It neither drops
  small coefficients nor changes tolerances. Candidate and revalidation work
  share the existing two-million-term batch budget.
* Merging requires equal supports, exactly proportional coefficients, compatible
  objective coefficients and exactly representable aggregate bounds. Hashes
  only shortlist candidates; exact comparisons prove proportionality. Negative
  factors and several donors are supported.
* Dominance here means **specialized proportional-column capacity dominance**.
  Exact row activities bound the aggregate coordinate; another column must have
  enough capacity to replace the donor without worsening the objective. The
  existing pair/term limits are one million and twenty million. General
  nonproportional dominance remains outside this option.

Compact owned records restore tail maps, fixed columns, merged columns, row
multipliers and the original base maps. Native reconstruction conserves the
aggregate exactly and retains the original tolerance bands. Basis/dual proposals
still go through original-model cleanup, refactorization and certification.
Missing or unsafe hints use existing original-model recovery. Optional failure
never supplies a new proof of original infeasibility. Stop requests discard an
unfinished optional batch; the solve's existing deadline handling remains in
force.

## Work and memory

Disabled passes build no optional row index, proportionality groups, exact cache
or undo history. The helper's union return may box its existing immutable result
(144 bytes in the focused Julia 1.13 ARM64 check), a fixed setup cost independent
of model dimensions. The new options add three Boolean fields, copied during
option reconstruction.

Enabled setup builds row or support indices with work proportional to dimensions
and nonzeros before bounded candidate work. Merge and dominance share support
and exact-value data while the matrix is identical; a changed CSC invalidates
support groups. Scalar exact-value cache entries remain valid. Cache entries are
limited to 100,000; BigFloat payloads additionally have a 64 MiB cap. Caches and
indices expire before simplex. No intermediate models, diagnostic snapshots or
basis factors are retained by optional postsolve records.

Restoration uses dimension-sized vectors and scalar undo records. It does not
factor an additional intermediate basis. Original cleanup remains authoritative.
For primal solves with artificial variables, completed phase II can export its
existing certificate dual without another BTRAN. Mapping this dual is separately
checked on the original pre-phase-I model; the required final feasibility and
reduced-cost scans occur only when the optional witness is requested. This
preserves the internal certified-witness contract and avoids an otherwise
unnecessary fresh solve. The default-off path does not capture it.

These options can change the reduced model and simplex trajectory. Fewer
iterations alone are not a kernel speedup; no universal performance improvement
is promised. Integration validation uses targeted tests and small complete LPs,
not another medium/largo solve.
