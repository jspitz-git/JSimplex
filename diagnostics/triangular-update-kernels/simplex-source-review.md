# Comparison with the local Simplex.jl basis managers

Read-only inspection requested by the user. Source revision:
`0d7feea4fec84cc55535672e59546f0a6fe27a74`, clean checkout at
`/home/jspitz/Simplex.jl`. No Simplex.jl files were changed or benchmarked.
The user reports that BGTransform was extremely slow. Its presence in this
review does not constitute a performance recommendation.

## Algorithms behind the names

`src/basisManagers/ft.jl:534` stores the tableau column and pivot. Its
`applyFTColumnUpdate` at line 580 computes `theta = v[p] / d[p]`, subtracts
`theta * d[i]` from the other entries, and writes `theta` at the pivot.
FTRAN at line 618 solves the original LU and applies those updates in order;
BTRAN applies their transposes in reverse before the original LU transpose.
This is an eta/product-form operation, despite the Forrest-Tomlin name.
It does not maintain and retriangularize an updated U factor.

The ordinary `BartelsGolubManager` has the same distinction:
`bg.jl:12476` applies the same column operation; `bg.jl:13175` solves the
original factor and applies the column-update chain. It must not be confused
with `BartelsGolubTransformState`. The factory distinguishes the two at
`src/simplex/basis_manager_factory.jl:21`.

Consequently, fast ordinary FT/BG timings in Simplex.jl are not evidence that
its true triangular update machinery is faster. There is no Suhl-Suhl manager
in the inspected basis-manager directory/factory.

## Potentially transferable details

| Mechanism | Source | Relevance to JSimplex |
|---|---|---|
| Stable stored column identities with a logical permutation map | `bg.jl:3293`, `bgShiftedColumnMapDeleteAppend!` at 3361 | Avoids rewriting every stored column index on a logical shift. JSimplex BG already uses stable column identities for row incidence; FT/SS still physically shift packed row indices. A corresponding stable row representation is a candidate, not a measured improvement. |
| Retained sparse rows, touched-row clearing, changed-column counts | `bg.jl:3300`, 6060, 6069 | Supports local maintenance instead of repeated full reconstruction. Must be paired with both FTRAN and BTRAN and with cancellation/fill-in tests. Current BG incidence already implements part of this idea. |
| Optional solves directly from sparse rows and their map | `bg.jl:7343`, 7403, 7532, 8289 | Can avoid converting update storage for each solve. The switch defaults to false at line 3445; availability does not establish speed. |
| Pivot handled outside coefficient loops | `ft.jl:580`, 595 | Removes a branch per update coefficient. A local split-diagonal prototype for our U solves showed a small kernel benefit, but it is not part of the prepared-spike feature and needs separate validation. |
| Sparse tableau support passed into replacement | `ft.jl:552` | Avoids scanning the full direction to build an update. JSimplex already has indexed/hypersparse infrastructure; legacy dense runs do not automatically obtain this benefit. |

Scratch/storage reuse and UMFPACK reuse also exist in Simplex.jl. Allocation
work is explicitly outside this task, and JSimplex already recycles update
buffers. No changes are justified merely by the existence of those caches.

## Structural lesson and limits

BGTransform starts from separate L/U factors and applies a row-transform chain
between the L and U solves (`bg.jl:7509`, 7562). JSimplex currently solves the
complete original LU and then an additional upper correction factor. This
explains a structural source of additional work, but removing it alone is not
a proven optimization: our direct-LU prototype was slower with the current
update kernels, consistent with the user's BGTransform experience.

There is also a concrete cost in the inspected BGTransform update path:
`bgSparseShiftedUpperReductionNoCopy!` calls `bgSparseRowsMatrix!` after
triangularization (`bg.jl:5834`, also 5918). The context overload at line 4281
recomputes column pointers and fills the CSC entries from all retained rows.
Stable column IDs therefore do not eliminate the full-factor conversion.
Direct sparse-row solves alone do not remove that unconditional update cost.
This is a source-level observation, not a measured attribution of the user's
slow BGTransform run.

The next representation experiment should isolate stable row identities and
incremental incidence, measuring replacement plus both solve directions on the
same recorded exchanges. It must preserve deterministic arithmetic order or
explicitly validate the numerical change. Only after that measurement should
changing the initial LU representation be reconsidered. No BGTransform code,
fixed drop thresholds, or adaptive policies were copied into this branch.
